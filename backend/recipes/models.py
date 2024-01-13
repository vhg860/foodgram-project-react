from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from api.constans import (LIMIT_TEXT, MAX_AMOUNT, MAX_LENGHT_COLOR,
                          MAX_LENGHT_NAME, MAX_LENGHT_SLUG, MAX_LENGHT_UNIT,
                          MIN_AMOUNT)
from recipes.utils import generate_color
from users.models import CustomUser


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        verbose_name='Название тега',
        max_length=MAX_LENGHT_NAME,
        unique=True,
        help_text='Введите название тега'
    )
    color = ColorField(
        verbose_name='Цвет в HEX',
        max_length=MAX_LENGHT_COLOR,
        unique=True,
        help_text='Введите цвет тега в формате HEX (#RRGGBB)',
        default=generate_color,
    )
    slug = models.SlugField(
        verbose_name='Slug тега',
        max_length=MAX_LENGHT_SLUG,
        unique=True,
        help_text='Slug тега'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:LIMIT_TEXT]


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGHT_NAME,
        help_text='Введите название ингредиента'
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=MAX_LENGHT_UNIT,
        help_text='Введите единицы измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='ingredient_name_measurement_unit'
            )
        ]

    def __str__(self):
        return f'{self.name[:LIMIT_TEXT]},{self.measurement_unit[:LIMIT_TEXT]}'


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='images/',
        null=True,
        default=None,
        help_text='Загрузите изображение блюда'
    )
    name = models.CharField(
        verbose_name='Название рецепта/блюда',
        max_length=MAX_LENGHT_NAME,
        help_text='Введите название для рецепта/блюда'
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Добавьте описание рецепта'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        default=1,
        validators=[
            MinValueValidator(
                1,
                message='Время приготовления не может быть меньше 1 минуты'
            ),
            MaxValueValidator(
                1000,
                message='Время приготовления не может быть больше 1000 минут'
            )
        ],
        help_text='Введите время приготовления в минутах (от 1 до 1000)'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        help_text='Дата автоматически заполняется при публикации'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'

    def __str__(self):
        return self.name[:LIMIT_TEXT]


class BaseShoppingCart_Favorite(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        ordering = ['user', 'recipe']


class ShoppingCart(BaseShoppingCart_Favorite):
    """Модель списка покупок."""

    class Meta(BaseShoppingCart_Favorite.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_cart'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_shopping_cart'
            )
        ]

    def __str__(self):
        return (
            f'{self.user.username} добавил в список покупок '
            f'{self.recipe.name}'
        )


class Favorite(BaseShoppingCart_Favorite):
    """Модель избранных рецептов."""

    class Meta(BaseShoppingCart_Favorite.Meta):
        verbose_name = "Избранный"
        verbose_name_plural = "Избранные"
        default_related_name = 'favorites'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_favorite_recipe'
            )
        ]

    def __str__(self):
        return (
            f'Рецепт {self.recipe} добавлен в избранное '
            f'пользователем {self.user}'
        )


class IngredientInRecipe(models.Model):
    """Модель связи ингредиентов в рецепте."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='ingredient_in_recipe'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество ингредиента в рецепте",
        default=1,
        validators=[
            MinValueValidator(MIN_AMOUNT, message=f'Минимум: {MIN_AMOUNT}'),
            MaxValueValidator(MAX_AMOUNT, message=f'Максимум: {MAX_AMOUNT}')
        ],
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        default_related_name = 'ingredient_recipes'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return (
            f'Рецепт: {self.recipe}, Ингредиент: {self.ingredient}, '
            f'Количество: {self.amount}'
        )
