from io import BytesIO

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from users.models import CustomUser, Subscription

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination, NonePagination
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeDetailSerializer, RecipeInfoSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserDetailSerializer)


class UserViewSet(UserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserDetailSerializer
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get("id")
        author = get_object_or_404(CustomUser, id=author_id)

        if request.method == "POST":
            serializer = SubscriptionSerializer(
                author,
                data=request.data,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            subscription = Subscription.objects.filter(
                user=user, author=author).first()
            if not subscription:
                return Response({"error": "Подписки не существует"},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = CustomUser.objects.filter(following__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages,
            many=True,
            context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        user = request.user
        serializer = UserDetailSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для просмотра тегов"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = NonePagination


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для просмотра ингредиентов"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = NonePagination


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для просмотра и редактирования рецептов"""

    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrAdminOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Определение, какой сериализатор использовать"""

        if self.request.method in SAFE_METHODS:
            return RecipeDetailSerializer
        return RecipeCreateUpdateSerializer

    def add_to(self, model, user, pk):
        if not Recipe.objects.filter(id=pk).exists():
            raise exceptions.ValidationError(
                "Выбранного рецепта не существует"
            )
        if model.objects.filter(user=user, recipe__id=pk).exists():
            raise exceptions.ValidationError(
                "Рецепт уже добавлен"
            )
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeInfoSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, pk):
        if not model.objects.filter(
            user=user.id, recipe=get_object_or_404(Recipe, id=pk)
        ).exists():
            raise exceptions.ValidationError(
                f"Указанного рецепта нет в {model}"
            )
        model.objects.filter(user=user, recipe__id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.add_to(Favorite, request.user, pk)
        return self.delete_from(Favorite, request.user, pk)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_to(ShoppingCart, request.user, pk)
        return self.delete_from(ShoppingCart, request.user, pk)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Загрузка списка покупок ингредиентов в виде текстового файла"""

        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=HTTP_400_BAD_REQUEST)

        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=request.user).values(
                "ingredient__name",
                "ingredient__measurement_unit").annotate(amount=Sum('amount'))

        today = now()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="{user.username}_shopping_list.pdf"'
        )

        buffer = BytesIO()

        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle(f"{user.username} Shopping List")

        pdf.drawString(100, 750, f"Список покупок для: {user.get_full_name()}")
        pdf.drawString(100, 730, f"Дата: {today:%d-%m-%Y}")
        pdf.drawString(100, 710, "Ингредиенты:")

        y = 690
        for ingredient in ingredients:
            text = (
                f'- {ingredient["ingredient__name"]} '
                f'({ingredient["ingredient__measurement_unit"]}) - '
                f'{ingredient["amount"]}'
            )
            pdf.drawString(100, y, text)
            y -= 20

        pdf.drawString(
            100, y - 20, f"Foodgram ({today:%Y})"
        )
        pdf.save()

        buffer.seek(0)
        response.write(buffer.getvalue())
        buffer.close()

        return response
