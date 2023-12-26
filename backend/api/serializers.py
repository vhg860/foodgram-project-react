from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag
from users.models import CustomUser

from .constans import (DUPLICATE_SUBSCRIPTION_ERROR, MIN_COOKING_TIME,
                       MIN_INGREDIENT_COUNT, MIN_TAG_COUNT,
                       SELF_SUBSCRIPTION_ERROR)
from .fields import Base64ImageField


class UserDetailSerializer(UserSerializer):
    """Сериализатор для получения детальной информации о пользователях."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        """Проверяет подписан ли пользователь."""
        request = self.context.get("request")

        return bool(
            request and request.user.is_authenticated
            and request.user.followers.filter(author=obj).exists()
        )


class UserRegistrationSerializer(UserCreateSerializer):
    """Сериализатор для регистрации новых пользователей."""

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для информации о подписках пользователя."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        """Проверяет подписан ли пользователь."""
        request = self.context.get("request")

        return bool(
            request and request.user.is_authenticated
            and request.user.followers.filter(author=obj).exists()
        )

    def validate(self, data):
        """Проверяет валидность данных."""
        author_id = self.context.get(
            'request').parser_context.get("kwargs").get("id")
        author = get_object_or_404(CustomUser, id=author_id)
        user = self.context.get("request").user

        if user.followers.filter(author=author_id).exists():
            raise ValidationError(
                detail=DUPLICATE_SUBSCRIPTION_ERROR,
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail=SELF_SUBSCRIPTION_ERROR,
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов пользователя."""
        return Recipe.objects.filter(author=obj).count()

    def get_recipes(self, obj):
        """Возвращает информацию о рецептах пользователя."""
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")
        recipes_queryset = obj.recipes.all()

        if recipes_limit is not None:
            recipes_queryset = recipes_queryset[:int(recipes_limit)]

        serializer = RecipeInfoSerializer(
            recipes_queryset,
            many=True,
            context=self.context
        )
        return serializer.data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = "__all__"


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиентов рецепта."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(1, message='Минимум: 1 единица'),
            MaxValueValidator(1000, message='Максимум: 1000 единиц')
        ]
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            "id",
            "amount",
        )


class RecipeInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для получения основной информации о рецептах."""

    image = Base64ImageField(
        read_only=True,
        help_text="Изображение рецепта в формате Base64"
    )
    name = serializers.ReadOnlyField(
        help_text="Название рецепта"
    )
    cooking_time = serializers.ReadOnlyField(
        help_text="Время приготовления в минутах"
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time"
        )


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для получения информации о рецептах."""

    image = Base64ImageField()
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = UserDetailSerializer(
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField(
        read_only=True,
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        read_only=True,
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_ingredients(self, obj):
        """Получает ингредиенты рецепта иподсчитывает количество каждого."""
        recipe = obj

        ingredients = recipe.ingredients.annotate(
            amount=Sum("ingredient_recipes__amount")
        ).values("id", "name", "measurement_unit", "amount")
        return ingredients

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное у пользователя."""
        user = self.context.get("request").user

        return bool(
            user and not user.is_anonymous
            and user.favorites.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, есть ли рецепт в списке покупок у пользователя."""
        user = self.context.get("request").user

        return bool(
            user and not user.is_anonymous
            and user.shopping_cart.filter(recipe=obj).exists()
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientInRecipeCreateSerializer(
        many=True
    )
    author = UserDetailSerializer(
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        """Валидация данных (ingredients, tags, cooking_time, image)."""
        ingredients = data.get("ingredients", [])
        tags = data.get("tags", [])
        cooking_time = data.get("cooking_time", 0)
        image = data.get("image")

        if not tags:
            raise serializers.ValidationError(
                f"Рецепт должен содержать как минимум {MIN_TAG_COUNT} тег"
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError("Теги не должны повторяться")

        if not ingredients:
            raise serializers.ValidationError(
                f"Рецепт должен содержать как минимум "
                f"{MIN_INGREDIENT_COUNT} ингредиент"
            )
        ingredients_list = set()
        for ingredient in ingredients:
            ingredient_id = ingredient.get("id")
            amount = ingredient.get("amount")
            if amount < MIN_INGREDIENT_COUNT:
                raise serializers.ValidationError(
                    f"Количество ингредиента не может быть меньше "
                    f"{MIN_INGREDIENT_COUNT}"
                )
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError("Ингредиент не существует")
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError(
                    "Ингредиент уже добавлен в рецепт"
                )
            ingredients_list.add(ingredient_id)

        if cooking_time < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                f"Время готовки не может быть менее {MIN_COOKING_TIME} мин"
            )

        if not image:
            raise serializers.ValidationError(
                ("Добавьте изображение")
            )

        return data

    def create_ingredients_recipes(self, ingredients, recipe):
        """Создает связи между рецептом и ингредиентами."""
        ingredient_instances = [
            IngredientInRecipe(
                ingredient=ingredient["id"],
                recipe=recipe,
                amount=ingredient["amount"]
            ) for ingredient in ingredients
        ]
        IngredientInRecipe.objects.bulk_create(ingredient_instances)

    def create(self, validated_data):
        """Создание нового рецепта с связанными ингредиентами."""
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_recipes(recipe=recipe, ingredients=ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        instance.image = validated_data.get("image", instance.image)
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        ingredients_data = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        instance.tags.clear()
        instance.tags.set(tags)
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients_recipes(
            recipe=instance,
            ingredients=ingredients_data
        )
        instance.save()
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Преобразует объект рецепта в сериализованный формат."""
        return RecipeDetailSerializer(instance, context=self.context).data
