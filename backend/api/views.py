from io import BytesIO

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination, NonePagination
from api.permissions import IsOwnerOrAdminOrReadOnly
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeDetailSerializer,
                             ShoppingCartSerializer,
                             SubscriptionSerializer,
                             SubscriptionInfoSerializer,
                             TagSerializer,
                             UserDetailSerializer)
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import CustomUser, Subscription


class UserViewSet(UserViewSet):
    """Представление для пользователя."""
    queryset = CustomUser.objects.all()
    serializer_class = UserDetailSerializer
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        """Управление созданием/удалением подписки."""
        author = get_object_or_404(
            CustomUser,
            id=self.kwargs.get('id'),
        )
        data = {'user': request.user.id, 'author': author.id}
        serializer = SubscriptionInfoSerializer(
            data=data,
            context={'request': request}
        )

        if request.method == 'POST':
            return self.create_subscription(serializer)
        elif request.method == 'DELETE':
            return self.delete_subscription(request.user, author)

    def create_subscription(self, serializer):
        """Создание подписки."""
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_subscription(self, user, author):
        """Удаление подписки."""
        subscription = Subscription.objects.filter(
            user=user,
            author=author
        ).first()
        if not subscription:
            return Response(
                {"error": "Подписки не существует"},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Возвращает список подписок текущего пользователя."""
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
        """Возвращает информацию о текущем пользователе."""
        user = request.user
        serializer = UserDetailSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для просмотра тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = NonePagination


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для просмотра ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = NonePagination


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для просмотра и редактирования рецептов"""

    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrAdminOrReadOnly, IsAuthenticatedOrReadOnly)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        """Создает рецепт с указанием автора."""
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Определение, какой сериализатор использовать."""
        if self.request.method in SAFE_METHODS:
            return RecipeDetailSerializer
        return RecipeCreateUpdateSerializer

    def add_to(self, request, pk, serializer_class):
        """Добавляет рецепт для пользователя."""
        try:
            recipe = Recipe.objects.get(
                id=pk,
            )
        except Recipe.DoesNotExist:
            return Response(
                {'errors': 'Рецепта не существует'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = serializer_class(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, pk):
        """Удаляет рецепт для пользователя."""
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
        """Удаляет/добавляет рецепт в избранное."""
        if request.method == 'POST':
            return self.add_to(request, pk, FavoriteSerializer)
        return self.delete_from(Favorite, request.user, pk)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        """Удаляет/добавляет рецепт в корзину."""
        if request.method == 'POST':
            return self.add_to(request, pk, ShoppingCartSerializer)
        return self.delete_from(ShoppingCart, request.user, pk)

    def generate_shopping_list(self, request):
        """Генерация списка покупок в виде текстового файла."""
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=HTTP_400_BAD_REQUEST)

        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=request.user).values(
                "ingredient__name",
                "ingredient__measurement_unit").annotate(amount=Sum('amount'))

        today = now()

        shopping_list = []

        for ingredient in ingredients:
            text = (
                f'- {ingredient["ingredient__name"]} '
                f'({ingredient["ingredient__measurement_unit"]}) - '
                f'{ingredient["amount"]}'
            )
            shopping_list.append(text)

        shopping_list.append(f"Foodgram ({today:%Y})")

        return shopping_list

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Загрузка списка покупок ингредиентов в виде PDF файла."""
        shopping_list = self.generate_shopping_list(request)

        if isinstance(shopping_list, Response):
            return shopping_list

        today = now()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="{request.user.username}_shopping_list.pdf"'
        )

        buffer = BytesIO()

        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle(f"{request.user.username} Shopping List")

        pdf.drawString(100, 750,
                       f"Список покупок для:{request.user.get_full_name()}")
        pdf.drawString(100, 730, f"Дата: {today:%d-%m-%Y}")
        pdf.drawString(100, 710, "Ингредиенты:")

        y = 690
        for line in shopping_list:
            pdf.drawString(100, y, line)
            y -= 20

        pdf.drawString(
            100, y - 20, f"Foodgram ({today:%Y})"
        )
        pdf.save()

        buffer.seek(0)
        response.write(buffer.getvalue())
        buffer.close()

        return response
