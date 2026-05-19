from django.contrib import admin

from .models import (
    Recipe,
    Favorite,
    ShoppingItem,
    RecipeRating,
    UserQuery
)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "difficulty",
        "cooking_time",
        "calories",
        "rating"
    )

    search_fields = (
        "title",
        "ingredients"
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        "user_id",
        "recipe"
    )


@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    list_display = (
        "user_id",
        "product"
    )


@admin.register(RecipeRating)
class RecipeRatingAdmin(admin.ModelAdmin):
    list_display = (
        "user_id",
        "recipe",
        "stars"
    )


@admin.register(UserQuery)
class UserQueryAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "telegram_id",
        "message",
        "created_at"
    )

    search_fields = (
        "username",
        "message"
    )

    readonly_fields = (
        "telegram_id",
        "username",
        "message",
        "response",
        "created_at"
    )