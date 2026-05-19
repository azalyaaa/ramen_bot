from django.db import models


class Recipe(models.Model):
    title = models.CharField(max_length=200)
    ingredients = models.TextField()
    instructions = models.TextField()
    cooking_time = models.IntegerField(default=0)
    calories = models.IntegerField(default=0)
    proteins = models.FloatField(default=0)
    fats = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    difficulty = models.CharField(max_length=50, default="easy")
    rating = models.FloatField(default=0)
    created_by = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return self.title


class Favorite(models.Model):
    user_id = models.BigIntegerField()
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)


class ShoppingItem(models.Model):
    user_id = models.BigIntegerField()
    product = models.CharField(max_length=100)


class RecipeRating(models.Model):
    user_id = models.BigIntegerField()
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    stars = models.IntegerField(default=5)


class UserQuery(models.Model):
    telegram_id = models.BigIntegerField()
    username = models.CharField(max_length=255)
    message = models.TextField()
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class UserRecipe(models.Model):
    user_id = models.BigIntegerField()
    name = models.CharField(max_length=200)
    ingredients = models.TextField()
    calories = models.IntegerField(default=0)
    proteins = models.FloatField(default=0)
    fats = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    cooking_time = models.CharField(max_length=100)
    recipe_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    class UserRecipe(models.Model):
        user_id = models.BigIntegerField()

    name = models.CharField(
        max_length=200
    )

    recipe_text = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name