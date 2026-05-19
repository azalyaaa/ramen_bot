import os
import sys
import re
import random
import threading
import time

from dotenv import load_dotenv

# Add project root to path BEFORE django.setup()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')

import django
django.setup()

import telebot
from telebot import types

from recipe_bot.models import UserQuery, UserRecipe

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN', '8739715609:AAF4djHaHUgBlyMbU_W00yPznl-xtP6-TkU')
bot = telebot.TeleBot(TOKEN)

# ========================
# IN-MEMORY STORAGE
# ========================
user_states = {}
user_favorites = {}   # {chat_id: set(recipe_name)}
user_ratings = {}     # {chat_id: {recipe_name: 1..5}}

# ========================
# RECIPES — MAIN (with nutrition per 100g)
# ========================
RECIPES = [
    {
        "name": "Fluffy Home Omelette",
        "ingredients": ["egg", "milk", "butter"],
        "time": "15 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 154 | P — 10g | F — 11g | C — 2g",
        "shopping_list": "🥚 Eggs — 3 pcs\n🥛 Milk — 150 ml\n🧈 Butter — 10g\n🧂 Salt, pepper",
        "full_recipe": (
            "🍳 *Fluffy Home Omelette*\n"
            "⏱ Time: ~15 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Eggs — 3 pcs\n"
            "• Milk — 150 ml\n"
            "• Butter — 10g\n"
            "• Salt, pepper\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Crack eggs, add salt and pepper\n"
            "2. Pour in milk, mix with a fork (don't beat)\n"
            "3. Melt butter in a pan, coat the sides\n"
            "4. Pour in mixture, cover with a lid\n"
            "5. Cook on low heat for 7–10 minutes"
        )
    },
    {
        "name": "Cheesy Ramen",
        "ingredients": ["noodles", "cheese", "egg", "ramen"],
        "time": "10 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 198 | P — 9g | F — 8g | C — 23g",
        "shopping_list": "🍜 Ramen noodles — 1 pack\n🧀 Cheddar cheese — 2 slices\n🥚 Boiled egg — 1 pc\n🌿 Green onion — to taste",
        "full_recipe": (
            "🍜 *Cheesy Ramen*\n"
            "⏱ Time: ~10 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Ramen noodles — 1 pack\n"
            "• Cheddar cheese — 2 slices\n"
            "• Boiled egg — 1 pc\n"
            "• Green onion to taste\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Cook noodles per package instructions (3–4 min)\n"
            "2. Transfer to a bowl\n"
            "3. Place cheese on top — it will melt from the heat\n"
            "4. Garnish with egg halves and onion"
        )
    },
    {
        "name": "Fried Rice with Chicken",
        "ingredients": ["rice", "chicken", "egg", "soy sauce"],
        "time": "20 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 165 | P — 12g | F — 5g | C — 18g",
        "shopping_list": "🍚 Cooked rice — 200g\n🍗 Chicken fillet — 150g\n🥚 Egg — 1 pc\n🫙 Soy sauce — 2 tbsp\n🌿 Green onion — 2–3 stalks",
        "full_recipe": (
            "🍚 *Fried Rice with Chicken*\n"
            "⏱ Time: ~20 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Cooked rice — 200g\n"
            "• Chicken fillet — 150g\n"
            "• Egg — 1 pc\n"
            "• Soy sauce — 2 tbsp\n"
            "• Green onion — 2–3 stalks\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Dice chicken, fry for 5 min on high heat\n"
            "2. Push chicken aside, crack in egg, stir quickly\n"
            "3. Add rice, mix well\n"
            "4. Pour in soy sauce, fry for another 2–3 min\n"
            "5. Sprinkle with green onion"
        )
    },
    {
        "name": "Caesar Salad with Chicken",
        "ingredients": ["chicken", "lettuce", "bread", "cheese"],
        "time": "25 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 130 | P — 11g | F — 7g | C — 6g",
        "shopping_list": "🍗 Chicken fillet — 200g\n🥬 Lettuce leaves — 100g\n🍞 White bread — 2 slices\n🧀 Parmesan — 30g\n🫙 Caesar dressing — 3 tbsp",
        "full_recipe": (
            "🥗 *Caesar Salad with Chicken*\n"
            "⏱ Time: ~25 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Chicken fillet — 200g\n"
            "• Iceberg lettuce — 100g\n"
            "• White bread — 2 slices\n"
            "• Parmesan — 30g\n"
            "• Caesar dressing — 3 tbsp\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Slice chicken, fry until golden\n"
            "2. Cut bread into cubes, toast in a dry pan\n"
            "3. Tear lettuce leaves by hand\n"
            "4. Place chicken and croutons on lettuce\n"
            "5. Drizzle with dressing, sprinkle with grated cheese"
        )
    },
    {
        "name": "Greek Salad",
        "ingredients": ["cucumber", "tomato", "olive", "feta", "pepper"],
        "time": "10 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 90 | P — 4g | F — 6g | C — 5g",
        "shopping_list": "🥒 Cucumber — 1 pc\n🍅 Tomato — 2 pcs\n🫒 Olives — handful\n🧀 Feta cheese — 100g\n🫑 Bell pepper — 1 pc\n🫙 Olive oil, lemon",
        "full_recipe": (
            "🥗 *Greek Salad*\n"
            "⏱ Time: ~10 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Cucumber — 1 pc\n"
            "• Tomato — 2 pcs\n"
            "• Olives — handful\n"
            "• Feta cheese — 100g\n"
            "• Bell pepper — 1 pc\n"
            "• Olive oil, lemon\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Chop all vegetables into large cubes\n"
            "2. Add olives and feta cubes\n"
            "3. Drizzle with olive oil and lemon juice\n"
            "4. Mix and serve"
        )
    },
    {
        "name": "Olivier Salad",
        "ingredients": ["potato", "carrot", "sausage", "cucumber", "egg", "peas", "mayo"],
        "time": "40 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 195 | P — 6g | F — 14g | C — 12g",
        "shopping_list": "🥔 Potatoes — 3 pcs\n🥕 Carrots — 2 pcs\n🥩 Boiled sausage — 200g\n🥒 Pickled cucumber — 2 pcs\n🥚 Eggs — 3 pcs\n🫛 Canned peas — 1 can\n🫙 Mayonnaise — 3 tbsp",
        "full_recipe": (
            "🥗 *Olivier Salad*\n"
            "⏱ Time: ~40 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Potatoes — 3 pcs\n"
            "• Carrots — 2 pcs\n"
            "• Boiled sausage — 200g\n"
            "• Pickled cucumbers — 2 pcs\n"
            "• Eggs — 3 pcs\n"
            "• Canned peas — 1 can\n"
            "• Mayonnaise — 3 tbsp\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Boil potatoes, carrots, and eggs\n"
            "2. Cool and dice into small cubes\n"
            "3. Dice sausage and cucumbers\n"
            "4. Mix everything together with peas\n"
            "5. Add mayonnaise, season with salt"
        )
    },
    {
        "name": "Tuna Salad",
        "ingredients": ["tuna", "tomato", "cucumber", "egg", "onion"],
        "time": "15 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 110 | P — 13g | F — 5g | C — 4g",
        "shopping_list": "🐟 Canned tuna — 1 can\n🍅 Tomato — 1 pc\n🥒 Cucumber — 1 pc\n🥚 Boiled eggs — 2 pcs\n🧅 Onion — ½ pc\n🫙 Olive oil, lemon",
        "full_recipe": (
            "🥗 *Tuna Salad*\n"
            "⏱ Time: ~15 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Canned tuna — 1 can\n"
            "• Tomato — 1 pc\n"
            "• Cucumber — 1 pc\n"
            "• Boiled eggs — 2 pcs\n"
            "• Onion — ½ pc\n"
            "• Olive oil, lemon\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Boil eggs, slice them\n"
            "2. Dice tomato, cucumber and onion\n"
            "3. Open tuna, drain the liquid\n"
            "4. Mix everything together\n"
            "5. Dress with oil and lemon juice"
        )
    },
    {
        "name": "Caprese",
        "ingredients": ["tomato", "mozzarella", "basil"],
        "time": "5 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 150 | P — 9g | F — 10g | C — 4g",
        "shopping_list": "🍅 Tomatoes — 2 pcs\n🧀 Mozzarella — 125g\n🌿 Fresh basil — bunch\n🫙 Olive oil, salt",
        "full_recipe": (
            "🥗 *Caprese*\n"
            "⏱ Time: ~5 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Tomatoes — 2 pcs\n"
            "• Mozzarella — 125g\n"
            "• Fresh basil — bunch\n"
            "• Olive oil, salt\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Slice tomatoes and mozzarella into rounds\n"
            "2. Alternate on plate: tomato–mozzarella\n"
            "3. Add basil leaves\n"
            "4. Drizzle with olive oil, season with salt"
        )
    },
    {
        "name": "Beef Steak",
        "ingredients": ["beef", "butter", "garlic", "rosemary"],
        "time": "15 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 220 | P — 26g | F — 13g | C — 0g",
        "shopping_list": "🥩 Beef steak — 300g\n🧈 Butter — 20g\n🧄 Garlic — 2 cloves\n🌿 Rosemary — sprig\n🧂 Salt, pepper",
        "full_recipe": (
            "🥩 *Beef Steak*\n"
            "⏱ Time: ~15 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Beef steak — 300g\n"
            "• Butter — 20g\n"
            "• Garlic — 2 cloves\n"
            "• Rosemary — sprig\n"
            "• Salt, pepper\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Take meat out ahead of time — bring to room temp\n"
            "2. Season with salt and pepper on both sides\n"
            "3. Heat pan to maximum\n"
            "4. Sear 3 min per side\n"
            "5. Add butter, garlic, rosemary — baste meat for 1 min\n"
            "6. Rest for 5 minutes before serving"
        )
    },
    {
        "name": "Pork Steak",
        "ingredients": ["pork", "garlic", "soy sauce", "honey"],
        "time": "40 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 240 | P — 20g | F — 16g | C — 3g",
        "shopping_list": "🥩 Pork — 300g\n🧄 Garlic — 3 cloves\n🫙 Soy sauce — 2 tbsp\n🍯 Honey — 1 tbsp\n🧂 Salt, pepper",
        "full_recipe": (
            "🥩 *Pork Steak*\n"
            "⏱ Time: ~40 minutes (with marinade)\n\n"
            "📦 *Ingredients:*\n"
            "• Pork — 300g\n"
            "• Garlic — 3 cloves\n"
            "• Soy sauce — 2 tbsp\n"
            "• Honey — 1 tbsp\n"
            "• Salt, pepper\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Mix soy sauce, honey and garlic\n"
            "2. Marinate meat for 30 minutes\n"
            "3. Fry 5 min per side over medium heat\n"
            "4. Rest for 3 minutes"
        )
    },
    {
        "name": "Salmon Steak",
        "ingredients": ["salmon", "lemon", "oil"],
        "time": "15 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 206 | P — 20g | F — 13g | C — 0g",
        "shopping_list": "🐟 Salmon — 300g\n🍋 Lemon — ½ pc\n🫙 Olive oil — 1 tbsp\n🌿 Dill, salt, pepper",
        "full_recipe": (
            "🐟 *Salmon Steak*\n"
            "⏱ Time: ~15 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Salmon — 300g\n"
            "• Lemon — ½ pc\n"
            "• Olive oil — 1 tbsp\n"
            "• Dill, salt, pepper\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Season fish with salt and pepper on both sides\n"
            "2. Heat pan with oil\n"
            "3. Fry 3–4 min per side\n"
            "4. Squeeze lemon juice over\n"
            "5. Sprinkle with dill"
        )
    },
    {
        "name": "Pasta Carbonara",
        "ingredients": ["pasta", "bacon", "egg", "parmesan", "spaghetti"],
        "time": "25 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 280 | P — 13g | F — 14g | C — 27g",
        "shopping_list": "🍝 Spaghetti — 200g\n🥓 Bacon — 100g\n🥚 Eggs — 2 pcs + 1 yolk\n🧀 Parmesan — 50g\n🧂 Salt, black pepper",
        "full_recipe": (
            "🍝 *Pasta Carbonara*\n"
            "⏱ Time: ~25 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Spaghetti — 200g\n"
            "• Bacon — 100g\n"
            "• Eggs — 2 pcs + 1 yolk\n"
            "• Parmesan — 50g\n"
            "• Salt, black pepper\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Cook spaghetti al dente\n"
            "2. Fry bacon until crispy\n"
            "3. Mix eggs with grated parmesan and pepper\n"
            "4. Turn off heat under bacon\n"
            "5. Add hot pasta to bacon\n"
            "6. Pour in egg-cheese mixture, mix\n"
            "7. Add pasta water if needed"
        )
    },
    {
        "name": "Pasta Bolognese",
        "ingredients": ["pasta", "minced meat", "tomato", "onion", "carrot"],
        "time": "40 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 190 | P — 10g | F — 8g | C — 20g",
        "shopping_list": "🍝 Pasta — 200g\n🥩 Ground beef/pork — 300g\n🍅 Tomatoes — 200g\n🧅 Onion — 1 pc\n🥕 Carrot — 1 pc\n🧄 Garlic, salt, pepper",
        "full_recipe": (
            "🍝 *Pasta Bolognese*\n"
            "⏱ Time: ~40 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Pasta — 200g\n"
            "• Ground meat (beef/pork) — 300g\n"
            "• Tomatoes — 200g\n"
            "• Onion — 1 pc\n"
            "• Carrot — 1 pc\n"
            "• Garlic, salt, pepper\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Finely chop onion and carrot, fry for 5 min\n"
            "2. Add meat, cook breaking up lumps for 10 min\n"
            "3. Add tomatoes, salt, pepper\n"
            "4. Simmer on low heat for 20 min\n"
            "5. Cook pasta, serve with sauce"
        )
    },
    {
        "name": "Pasta Alfredo",
        "ingredients": ["pasta", "cream", "cheese", "butter", "garlic"],
        "time": "20 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 260 | P — 8g | F — 14g | C — 26g",
        "shopping_list": "🍝 Pasta — 200g\n🥛 Cream 20% — 200 ml\n🧀 Parmesan — 50g\n🧈 Butter — 20g\n🧄 Garlic — 2 cloves",
        "full_recipe": (
            "🍝 *Pasta Alfredo*\n"
            "⏱ Time: ~20 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Pasta — 200g\n"
            "• Cream 20% — 200 ml\n"
            "• Parmesan — 50g\n"
            "• Butter — 20g\n"
            "• Garlic — 2 cloves\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Cook pasta\n"
            "2. Sauté garlic in butter for 1 minute\n"
            "3. Add cream, warm for 3 minutes\n"
            "4. Add grated parmesan, mix\n"
            "5. Combine with pasta"
        )
    },
    {
        "name": "Pasta with Chicken and Mushrooms",
        "ingredients": ["pasta", "chicken", "mushroom", "cream", "garlic"],
        "time": "30 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 200 | P — 12g | F — 8g | C — 20g",
        "shopping_list": "🍝 Pasta — 200g\n🍗 Chicken fillet — 200g\n🍄 Champignons — 150g\n🥛 Cream — 150 ml\n🧄 Garlic — 2 cloves",
        "full_recipe": (
            "🍝 *Pasta with Chicken and Mushrooms*\n"
            "⏱ Time: ~30 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Pasta — 200g\n"
            "• Chicken fillet — 200g\n"
            "• Mushrooms (champignons) — 150g\n"
            "• Cream — 150 ml\n"
            "• Garlic — 2 cloves\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Cook pasta\n"
            "2. Slice chicken and mushrooms, fry with garlic for 8 min\n"
            "3. Add cream, simmer for 5 minutes\n"
            "4. Mix with pasta, season with salt"
        )
    },
    {
        "name": "Pasta Arrabbiata",
        "ingredients": ["pasta", "tomato", "garlic", "chili pepper"],
        "time": "20 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 150 | P — 5g | F — 3g | C — 26g",
        "shopping_list": "🍝 Pasta — 200g\n🍅 Canned tomatoes — 400g\n🧄 Garlic — 3 cloves\n🌶 Chili pepper — 1 pc\n🫙 Olive oil",
        "full_recipe": (
            "🍝 *Pasta Arrabbiata*\n"
            "⏱ Time: ~20 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Pasta — 200g\n"
            "• Canned tomatoes — 400g\n"
            "• Garlic — 3 cloves\n"
            "• Chili pepper — 1 pc\n"
            "• Olive oil\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Fry garlic and chili in oil for 2 minutes\n"
            "2. Add tomatoes, simmer for 10 minutes\n"
            "3. Cook pasta\n"
            "4. Mix with sauce"
        )
    },
    {
        "name": "Margherita Pizza",
        "ingredients": ["dough", "tomato", "mozzarella", "basil"],
        "time": "30 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 220 | P — 10g | F — 8g | C — 27g",
        "shopping_list": "🫓 Pizza dough — 250g\n🍅 Tomato sauce — 3 tbsp\n🧀 Mozzarella — 125g\n🌿 Basil — few leaves",
        "full_recipe": (
            "🍕 *Margherita Pizza*\n"
            "⏱ Time: ~30 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Pizza dough — 250g\n"
            "• Tomato sauce — 3 tbsp\n"
            "• Mozzarella — 125g\n"
            "• Basil — few leaves\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Preheat oven to 220°C\n"
            "2. Roll out dough\n"
            "3. Spread tomato sauce\n"
            "4. Place mozzarella slices\n"
            "5. Bake for 15–20 minutes\n"
            "6. Add fresh basil after baking"
        )
    },
    {
        "name": "Chicken Pilaf",
        "ingredients": ["rice", "chicken", "carrot", "onion", "garlic"],
        "time": "60 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 175 | P — 10g | F — 6g | C — 20g",
        "shopping_list": "🍚 Rice — 300g\n🍗 Chicken — 500g\n🥕 Carrot — 2 pcs\n🧅 Onion — 2 pcs\n🧄 Garlic — 1 head\n🫙 Oil, cumin, salt, pepper",
        "full_recipe": (
            "🍚 *Chicken Pilaf*\n"
            "⏱ Time: ~60 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Rice — 300g\n"
            "• Chicken — 500g\n"
            "• Carrot — 2 pcs\n"
            "• Onion — 2 pcs\n"
            "• Garlic — 1 head\n"
            "• Oil, cumin, salt, pepper\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Fry onion until golden\n"
            "2. Add chicken, fry for 10 min\n"
            "3. Add julienned carrot, fry for 5 min\n"
            "4. Cover with water 2 fingers above chicken\n"
            "5. Add washed rice in an even layer\n"
            "6. Push in garlic head, add spices\n"
            "7. Cook covered on low heat for 25 min"
        )
    },
    {
        "name": "Cottage Cheese Pancakes",
        "ingredients": ["cottage cheese", "egg", "flour", "sugar"],
        "time": "25 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 215 | P — 11g | F — 7g | C — 26g",
        "shopping_list": "🧀 Cottage cheese — 300g\n🥚 Egg — 1 pc\n🌾 Flour — 4 tbsp + for coating\n🍬 Sugar — 2 tbsp\n🍬 Vanilla — pinch\n🧂 Salt — pinch",
        "full_recipe": (
            "🧇 *Cottage Cheese Pancakes*\n"
            "⏱ Time: ~25 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Cottage cheese — 300g\n"
            "• Egg — 1 pc\n"
            "• Flour — 4 tbsp\n"
            "• Sugar — 2 tbsp\n"
            "• Vanilla, salt — pinch\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Mix cottage cheese, egg, sugar and vanilla\n"
            "2. Add flour, mix into dough\n"
            "3. Shape round pancakes, coat in flour\n"
            "4. Fry over medium heat 3–4 min per side\n"
            "5. Serve with sour cream or jam"
        )
    },
    {
        "name": "Kefir Pancakes",
        "ingredients": ["kefir", "egg", "flour", "sugar", "baking soda"],
        "time": "20 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 200 | P — 6g | F — 4g | C — 35g",
        "shopping_list": "🥛 Kefir — 300 ml\n🥚 Egg — 1 pc\n🌾 Flour — 200g\n🍬 Sugar — 2 tbsp\n🧪 Baking soda — ½ tsp\n🧂 Salt — pinch",
        "full_recipe": (
            "🥞 *Kefir Pancakes*\n"
            "⏱ Time: ~20 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Kefir — 300 ml\n"
            "• Egg — 1 pc\n"
            "• Flour — 200g\n"
            "• Sugar — 2 tbsp\n"
            "• Baking soda — ½ tsp\n"
            "• Salt — pinch\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Mix kefir, egg, sugar and salt\n"
            "2. Add soda, mix\n"
            "3. Add flour, stir to a thick batter\n"
            "4. Fry in oil by spoonful, 2–3 min per side\n"
            "5. Serve with sour cream or jam"
        )
    },
    {
        "name": "Baked Chicken with Vegetables",
        "ingredients": ["chicken", "potato", "carrot", "onion", "garlic"],
        "time": "60 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 150 | P — 12g | F — 6g | C — 11g",
        "shopping_list": "🍗 Chicken thighs — 4 pcs\n🥔 Potatoes — 4 pcs\n🥕 Carrots — 2 pcs\n🧅 Onion — 1 pc\n🧄 Garlic — 4 cloves\n🫙 Olive oil — 2 tbsp\n🧂 Salt, pepper, paprika",
        "full_recipe": (
            "🍗 *Baked Chicken with Vegetables*\n"
            "⏱ Time: ~60 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Chicken thighs — 4 pcs\n"
            "• Potatoes — 4 pcs\n"
            "• Carrots — 2 pcs\n"
            "• Onion — 1 pc\n"
            "• Garlic — 4 cloves\n"
            "• Olive oil, salt, paprika\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Preheat oven to 200°C\n"
            "2. Chop vegetables roughly\n"
            "3. Rub chicken with oil, salt and paprika\n"
            "4. Place everything in baking dish, add garlic\n"
            "5. Bake for 50–60 minutes\n"
            "6. Flip chicken 20 min before done"
        )
    },
    {
        "name": "Mashed Potatoes",
        "ingredients": ["potato", "milk", "butter"],
        "time": "30 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 100 | P — 2g | F — 4g | C — 14g",
        "shopping_list": "🥔 Potatoes — 6 pcs\n🥛 Hot milk — 150 ml\n🧈 Butter — 50g\n🧂 Salt to taste",
        "full_recipe": (
            "🥔 *Mashed Potatoes*\n"
            "⏱ Time: ~30 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Potatoes — 6 pcs\n"
            "• Hot milk — 150 ml\n"
            "• Butter — 50g\n"
            "• Salt\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Peel and chop potatoes, cover with cold water\n"
            "2. Bring to boil, salt, cook for 20 min\n"
            "3. Drain water, add butter\n"
            "4. Mash with a masher\n"
            "5. Pour in hot milk, whip until fluffy"
        )
    },
]

# ========================
# BAKING RECIPES (with nutrition per 100g)
# ========================
BAKING_RECIPES = [
    {
        "name": "Classic Sponge Cake",
        "ingredients": ["egg", "flour", "sugar"],
        "time": "45 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 265 | P — 7g | F — 4g | C — 50g",
        "shopping_list": "🥚 Eggs — 4 pcs\n🌾 Flour — 120g\n🍬 Sugar — 120g",
        "full_recipe": (
            "🎂 *Classic Sponge Cake*\n"
            "⏱ Time: ~45 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Eggs — 4 pcs\n"
            "• Flour — 120g\n"
            "• Sugar — 120g\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Preheat oven to 180°C\n"
            "2. Beat eggs with sugar until white foam (7–10 min)\n"
            "3. Sift flour, fold in gently with spatula\n"
            "4. Pour into lined mold\n"
            "5. Bake for 30–35 minutes\n"
            "6. Cool upside down"
        )
    },
    {
        "name": "Honey Cake",
        "ingredients": ["honey", "egg", "baking soda", "flour", "sour cream", "sugar"],
        "time": "90 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 310 | P — 5g | F — 11g | C — 47g",
        "shopping_list": "🍯 Honey — 3 tbsp\n🥚 Eggs — 2 pcs\n🍬 Sugar — 150g\n🧈 Butter — 50g\n🧪 Baking soda — 1 tsp\n🌾 Flour — 350g\n🫙 Sour cream 25% — 500g\n🍬 Powdered sugar — 150g",
        "full_recipe": (
            "🍯 *Honey Cake*\n"
            "⏱ Time: ~90 min + overnight soaking\n\n"
            "📦 *Ingredients:*\n"
            "• Honey — 3 tbsp\n"
            "• Eggs — 2 pcs\n"
            "• Sugar — 150g\n"
            "• Butter — 50g\n"
            "• Baking soda — 1 tsp\n"
            "• Flour — 350g\n"
            "• Sour cream 25% — 500g (cream)\n"
            "• Powdered sugar — 150g (cream)\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Melt honey, butter, sugar in a double boiler\n"
            "2. Add soda — mixture will foam\n"
            "3. Remove from heat, add eggs and flour\n"
            "4. Chill dough for 30 min\n"
            "5. Roll out 6–8 layers, bake 4 min each at 180°C\n"
            "6. Whip sour cream with powdered sugar\n"
            "7. Spread cream on each layer, refrigerate overnight"
        )
    },
    {
        "name": "Apple Charlotte",
        "ingredients": ["egg", "flour", "sugar", "apple"],
        "time": "55 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 190 | P — 5g | F — 2g | C — 38g",
        "shopping_list": "🥚 Eggs — 3 pcs\n🍬 Sugar — 150g\n🌾 Flour — 150g\n🍎 Apples — 3 pcs\n🧪 Baking powder — 1 tsp",
        "full_recipe": (
            "🍎 *Apple Charlotte*\n"
            "⏱ Time: ~55 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Eggs — 3 pcs\n"
            "• Sugar — 150g\n"
            "• Flour — 150g\n"
            "• Apples — 3 pcs\n"
            "• Baking powder — 1 tsp\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Preheat oven to 180°C\n"
            "2. Beat eggs with sugar until foamy\n"
            "3. Add flour with baking powder, mix\n"
            "4. Peel apples, dice them\n"
            "5. Fold apples into batter\n"
            "6. Bake for 40 minutes until golden"
        )
    },
    {
        "name": "Cherry Pie",
        "ingredients": ["flour", "butter", "sugar", "egg", "cherry"],
        "time": "60 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 240 | P — 4g | F — 10g | C — 33g",
        "shopping_list": "🌾 Flour — 300g\n🧈 Butter — 150g\n🍬 Sugar — 150g\n🥚 Eggs — 2 pcs\n🍒 Cherries — 300g\n🧪 Baking powder — 1 tsp",
        "full_recipe": (
            "🍒 *Cherry Pie*\n"
            "⏱ Time: ~60 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Flour — 300g\n"
            "• Butter — 150g\n"
            "• Sugar — 150g\n"
            "• Eggs — 2 pcs\n"
            "• Cherries — 300g\n"
            "• Baking powder — 1 tsp\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Preheat oven to 180°C\n"
            "2. Beat butter with sugar\n"
            "3. Add eggs one by one\n"
            "4. Fold in flour with baking powder\n"
            "5. Pour batter into mold\n"
            "6. Top with cherries\n"
            "7. Bake for 45 minutes"
        )
    },
    {
        "name": "Banana Bread",
        "ingredients": ["banana", "flour", "egg", "butter", "sugar"],
        "time": "70 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 250 | P — 4g | F — 8g | C — 40g",
        "shopping_list": "🍌 Ripe bananas — 3 pcs\n🌾 Flour — 200g\n🥚 Eggs — 2 pcs\n🧈 Butter — 80g\n🍬 Sugar — 100g\n🧪 Baking soda — 1 tsp",
        "full_recipe": (
            "🍌 *Banana Bread*\n"
            "⏱ Time: ~70 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Ripe bananas — 3 pcs\n"
            "• Flour — 200g\n"
            "• Eggs — 2 pcs\n"
            "• Butter — 80g\n"
            "• Sugar — 100g\n"
            "• Baking soda — 1 tsp\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Preheat oven to 175°C\n"
            "2. Mash bananas with a fork\n"
            "3. Mix with melted butter\n"
            "4. Add eggs and sugar\n"
            "5. Stir in flour and soda\n"
            "6. Pour into bread tin\n"
            "7. Bake for 55–60 minutes"
        )
    },
    {
        "name": "Oat Cookies",
        "ingredients": ["oats", "flour", "butter", "sugar", "egg"],
        "time": "25 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 390 | P — 7g | F — 18g | C — 50g",
        "shopping_list": "🌾 Oat flakes — 200g\n🌾 Flour — 100g\n🧈 Butter — 100g\n🍬 Sugar — 100g\n🥚 Egg — 1 pc\n🧪 Baking powder — ½ tsp",
        "full_recipe": (
            "🍪 *Oat Cookies*\n"
            "⏱ Time: ~25 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Oat flakes — 200g\n"
            "• Flour — 100g\n"
            "• Butter — 100g\n"
            "• Sugar — 100g\n"
            "• Egg — 1 pc\n"
            "• Baking powder — ½ tsp\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Preheat oven to 180°C\n"
            "2. Beat softened butter with sugar\n"
            "3. Add egg, mix\n"
            "4. Fold in oats, flour and baking powder\n"
            "5. Shape round cookies\n"
            "6. Bake for 12–15 minutes"
        )
    },
    {
        "name": "Fluffy Buns",
        "ingredients": ["flour", "milk", "yeast", "butter", "sugar", "egg"],
        "time": "120 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 290 | P — 8g | F — 8g | C — 45g",
        "shopping_list": "🌾 Flour — 500g\n🥛 Milk — 250 ml\n🧫 Dry yeast — 7g\n🧈 Butter — 80g\n🍬 Sugar — 60g\n🥚 Eggs — 2 pcs\n🧂 Salt — 1 tsp",
        "full_recipe": (
            "🥐 *Fluffy Buns*\n"
            "⏱ Time: ~2 hours\n\n"
            "📦 *Ingredients:*\n"
            "• Flour — 500g\n"
            "• Warm milk — 250 ml\n"
            "• Dry yeast — 7g\n"
            "• Butter — 80g\n"
            "• Sugar — 60g\n"
            "• Eggs — 2 pcs\n"
            "• Salt — 1 tsp\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Dissolve yeast in warm milk with 1 tsp sugar\n"
            "2. After 10 min add eggs, butter, sugar and salt\n"
            "3. Knead soft dough with flour\n"
            "4. Let rise for 1 hour in a warm place\n"
            "5. Shape buns, let proof for 20 min\n"
            "6. Brush with egg yolk, bake at 180°C for 20 min"
        )
    },
    {
        "name": "Cabbage Pies",
        "ingredients": ["flour", "egg", "kefir", "cabbage", "onion", "baking soda"],
        "time": "50 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 200 | P — 6g | F — 6g | C — 30g",
        "shopping_list": "🌾 Flour — 400g\n🥚 Eggs — 2 pcs\n🥛 Kefir — 250 ml\n🧪 Baking soda — 1 tsp\n🥬 Cabbage — ½ head\n🧅 Onion — 1 pc\n🧂 Salt, pepper",
        "full_recipe": (
            "🥟 *Cabbage Pies*\n"
            "⏱ Time: ~50 minutes\n\n"
            "📦 *Ingredients:*\n"
            "• Flour — 400g\n"
            "• Eggs — 2 pcs\n"
            "• Kefir — 250 ml\n"
            "• Baking soda — 1 tsp\n"
            "• Cabbage — ½ head\n"
            "• Onion — 1 pc\n"
            "• Salt, pepper\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Mix kefir, soda, eggs and flour — knead soft dough\n"
            "2. Shred cabbage, sauté with onion for 10 min, season\n"
            "3. Divide dough into balls, roll out\n"
            "4. Add filling, pinch pies shut\n"
            "5. Fry in oil 3–4 min per side"
        )
    },
    {
        "name": "Mug Cake (10 sec microwave)",
        "ingredients": ["flour", "egg", "sugar", "butter", "cocoa"],
        "time": "0.5 min",
        "nutrition": "🔢 *Nutrition per 100g:* cal — 320 | P — 7g | F — 14g | C — 42g",
        "shopping_list": "🌾 Flour — 4 tbsp\n🥚 Egg — 1 pc\n🍬 Sugar — 3 tbsp\n🧈 Butter — 2 tbsp\n🍫 Cocoa powder — 2 tbsp\n🥛 Milk — 3 tbsp\n🧂 Baking powder — ¼ tsp",
        "full_recipe": (
            "☕ *Mug Cake (10 sec microwave)*\n"
            "⏱ Time: ~10 seconds\n\n"
            "📦 *Ingredients:*\n"
            "• Flour — 4 tbsp\n"
            "• Egg — 1 pc\n"
            "• Sugar — 3 tbsp\n"
            "• Butter — 2 tbsp (melted)\n"
            "• Cocoa powder — 2 tbsp\n"
            "• Milk — 3 tbsp\n"
            "• Baking powder — ¼ tsp\n\n"
            "👨‍🍳 *How to cook:*\n"
            "1. Take a large mug (at least 300ml)\n"
            "2. Melt butter in it (10 sec in microwave)\n"
            "3. Add egg, milk, sugar — mix with a fork\n"
            "4. Add flour, cocoa, baking powder — mix until smooth\n"
            "5. Microwave on full power for 30 seconds\n"
            "6. Let it sit for 10 sec before eating\n\n"
            "💡 *Tip:* Don't overcook — it should be slightly moist in the middle!"
        )
    },
]

# Combined list for search
ALL_RECIPES = RECIPES + BAKING_RECIPES

# ========================
# SYNONYMS
# ========================
SYNONYMS = {
    "eggs": "egg", "egg": "egg",
    "chicken": "chicken", "hen": "chicken", "poultry": "chicken",
    "mushrooms": "mushroom", "mushroom": "mushroom", "champignons": "mushroom",
    "tomatoes": "tomato", "tomato": "tomato",
    "cucumbers": "cucumber", "cucumber": "cucumber",
    "oil": "oil", "butter": "butter",
    "cheese": "cheese",
    "onions": "onion", "onion": "onion",
    "garlic": "garlic",
    "pasta": "pasta", "spaghetti": "pasta", "noodles": "noodles",
    "dough": "dough",
    "flour": "flour",
    "milk": "milk",
    "potatoes": "potato", "potato": "potato",
    "carrots": "carrot", "carrot": "carrot",
    "beef": "beef",
    "pork": "pork",
    "salmon": "salmon", "trout": "salmon",
    "soy sauce": "soy sauce",
    "bacon": "bacon",
    "cream": "cream",
    "minced meat": "minced meat", "ground meat": "minced meat", "ground beef": "minced meat",
    "cabbage": "cabbage",
    "cottage cheese": "cottage cheese",
    "sugar": "sugar",
    "kefir": "kefir",
    "peas": "peas",
    "sausage": "sausage",
    "honey": "honey",
    "apples": "apple", "apple": "apple",
    "bananas": "banana", "banana": "banana",
    "cherries": "cherry", "cherry": "cherry",
    "oats": "oats", "oat flakes": "oats",
    "yeast": "yeast",
    "mayo": "mayo", "mayonnaise": "mayo",
    "olives": "olive", "olive": "olive",
    "feta": "feta",
    "mozzarella": "mozzarella",
    "basil": "basil",
    "rosemary": "rosemary",
    "lemon": "lemon",
    "rice": "rice",
    "tuna": "tuna",
    "cocoa": "cocoa",
    "cocoa powder": "cocoa",
    "chocolate": "cocoa",
    "mug": "mug",
    "microwave": "microwave",
}


# ========================
# SAVE TO DB
# ========================
def save_to_db(message, response):
    try:
        UserQuery.objects.create(
            telegram_id=message.from_user.id,
            username=message.from_user.username or message.from_user.first_name or "Unknown",
            message=message.text or "",
            response=response[:500]
        )
    except Exception as e:
        print(f"DB save error: {e}")


# ========================
# RECIPE SEARCH
# ========================
def normalize_keywords(text):
    words = [w.strip().lower() for w in text.replace(',', ' ').split()]
    return [SYNONYMS.get(w, w) for w in words if w]


def find_recipes_smart(text, recipe_list=None):
    if recipe_list is None:
        recipe_list = RECIPES
    keywords = normalize_keywords(text)
    total = len(keywords)
    scored = []
    for recipe in recipe_list:
        matches = sum(1 for ing in recipe['ingredients'] if ing in keywords)
        if matches >= 1:
            scored.append((matches, recipe))
    scored.sort(key=lambda x: x[0], reverse=True)
    groups = {}
    for score, recipe in scored:
        groups.setdefault(score, []).append(recipe)
    return groups, total, keywords


# ========================
# HELPER: get recipe by source
# ========================
def get_recipe_by_source(source, recipe_index):
    recipe_index = int(recipe_index)
    if source == "bake":
        return BAKING_RECIPES[recipe_index]
    return RECIPES[recipe_index]


def extract_minutes(recipe):
    time_text = recipe.get("time", "")
    # Handle fractional minutes like "0.5 min" (30 seconds)
    float_nums = re.findall(r"\d+\.\d+", time_text)
    if float_nums:
        return float(float_nums[0])
    nums = re.findall(r"\d+", time_text)
    if nums:
        return int(nums[0])
    return 10


# ========================
# MAIN MENU (Reply keyboard)
# ========================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🍳 Recipes"), types.KeyboardButton("📚 My Recipes"))
    markup.row(types.KeyboardButton("❤️ Favorites"), types.KeyboardButton("⭐ My Ratings"))
    markup.row(types.KeyboardButton("🛒 Shopping"), types.KeyboardButton("📅 Plan"))
    markup.row(types.KeyboardButton("➕ Add Recipe"), types.KeyboardButton("ℹ️ About"))
    return markup


# ========================
# /start
# ========================
@bot.message_handler(commands=['start'])
def start(message):
    user_states[message.chat.id] = 'waiting_products'
    text = (
        "👋 Hello! I'm a cooking bot 🍳\n\n"
        "Write down the ingredients you have at home, separated by commas:\n\n"
        "📝 *Example:* egg, milk, cheese\n"
        "or: chicken, rice, soy sauce\n\n"
        f"📚 Database: {len(ALL_RECIPES)} recipes!\n\n"
        "👇 Use the menu to navigate:"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu())
    save_to_db(message, text)


# ========================
# /help
# ========================
@bot.message_handler(commands=['help'])
def help_cmd(message):
    text = (
        "📖 *How to use the bot:*\n\n"
        "1️⃣ Write ingredients separated by commas\n"
        "2️⃣ I'll show matching recipes\n"
        "3️⃣ Tap on a recipe\n"
        "4️⃣ Get the full recipe with nutrition info!\n\n"
        "❤️ *Favorites* — saved recipes\n"
        "⭐ *Ratings* — rate a recipe\n"
        "➕ *Add Recipe* — add your own recipe\n"
        "🛒 *Shopping* — shopping list from recipe\n"
        "📅 *Plan* — weekly meal plan\n\n"
        "💡 *More ingredients = more accurate results!*\n\n"
        f"📚 Database: {len(ALL_RECIPES)} recipes"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu())
    save_to_db(message, text)


# ========================
# /plan — weekly meal plan
# ========================
@bot.message_handler(commands=['plan'])
def weekly_plan(message):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    recipes = random.sample(ALL_RECIPES, 21)

    text = "📅 *Random Weekly Meal Plan*\n\n"
    index = 0

    for day in days:
        breakfast = recipes[index]
        lunch = recipes[index + 1]
        dinner = recipes[index + 2]

        text += (
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🗓 *{day}*\n"
            f"🌅 Breakfast: {breakfast['name']}\n"
            f"🍽 Lunch: {lunch['name']}\n"
            f"🌙 Dinner: {dinner['name']}\n\n"
        )
        index += 3

    text += "💡 _A new plan with no repeats every time_"

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu())
    save_to_db(message, text[:500])


# ========================
# /about
# ========================
@bot.message_handler(commands=['about'])
def about(message):
    text = (
        "ℹ️ *About the bot*\n\n"
        "🍳 I'm your cooking assistant!\n\n"
        f"📚 Database: {len(ALL_RECIPES)} recipes:\n"
        f"• 🍽 Main dishes: {len(RECIPES)}\n"
        f"• 🎂 Baking: {len(BAKING_RECIPES)}\n\n"
        "✨ *Features:*\n"
        "• Search recipes by ingredients\n"
        "• Nutrition info per 100g\n"
        "• Add to favorites\n"
        "• Rate recipes ⭐\n"
        "• Add your own recipes\n"
        "• Shopping list\n"
        "• Weekly meal plan\n\n"
        "🛠 Version 2.0"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu())


# ========================
# SEND RECIPE
# ========================
def send_recipe(chat_id, recipe, recipe_index, source='main'):
    """Sends a recipe with favorite, rating, shopping and timer buttons."""
    text = recipe['full_recipe']
    nutrition = recipe.get('nutrition', '')
    if nutrition:
        text += f"\n\n{nutrition}"

    rating = user_ratings.get(chat_id, {}).get(recipe['name'])
    rating_str = f" {'⭐' * rating}" if rating else ""

    markup = types.InlineKeyboardMarkup(row_width=2)

    fav_btn = types.InlineKeyboardButton(
        "❤️ Add to Favorites",
        callback_data=f"fav_{source}_{recipe_index}"
    )
    shop_btn = types.InlineKeyboardButton(
        "🛒 Shopping List",
        callback_data=f"shop_{source}_{recipe_index}"
    )
    rate_btn = types.InlineKeyboardButton(
        f"⭐ Rate{rating_str}",
        callback_data=f"rate_{source}_{recipe_index}"
    )
    timer_btn = types.InlineKeyboardButton(
        "⏳ Set Timer",
        callback_data=f"timer_{source}_{recipe_index}"
    )

    markup.add(fav_btn)
    markup.row(shop_btn, rate_btn)
    markup.add(timer_btn)

    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)


# ========================
# RECIPE BUTTON HANDLERS
# ========================
@bot.callback_query_handler(func=lambda call: call.data.startswith('recipe_'))
def handle_recipe_button(call):
    parts = call.data.split('_')
    recipe_index = int(parts[1])
    recipe = RECIPES[recipe_index]
    bot.answer_callback_query(call.id)
    send_recipe(call.message.chat.id, recipe, recipe_index, source='main')


@bot.callback_query_handler(func=lambda call: call.data.startswith('bake_'))
def handle_bake_button(call):
    parts = call.data.split('_')
    recipe_index = int(parts[1])
    recipe = BAKING_RECIPES[recipe_index]
    bot.answer_callback_query(call.id)
    send_recipe(call.message.chat.id, recipe, recipe_index, source='bake')


@bot.callback_query_handler(func=lambda call: call.data.startswith('favrecipe_'))
def handle_fav_recipe_button(call):
    parts = call.data.split('_')
    source = parts[1]
    recipe_index = int(parts[2])
    recipe = get_recipe_by_source(source, recipe_index)
    bot.answer_callback_query(call.id)
    send_recipe(call.message.chat.id, recipe, recipe_index, source=source)


# ========================
# SHOPPING LIST
# ========================
@bot.callback_query_handler(func=lambda call: call.data.startswith('shop_'))
def handle_shopping_list(call):
    parts = call.data.split('_')
    source = parts[1]
    recipe_index = int(parts[2])
    recipe = get_recipe_by_source(source, recipe_index)
    bot.answer_callback_query(call.id)
    response_text = (
        f"🛒 *Shopping list for «{recipe['name']}»:*\n\n"
        f"{recipe['shopping_list']}\n\n"
        f"⏱ Cooking time: {recipe['time']}\n"
        f"{recipe.get('nutrition', '')}"
    )
    bot.send_message(call.message.chat.id, response_text, parse_mode='Markdown')


# ========================
# FAVORITES — ADD
# ========================
@bot.callback_query_handler(func=lambda call: call.data.startswith('fav_'))
def handle_add_favorite(call):
    parts = call.data.split('_')
    source = parts[1]
    recipe_index = int(parts[2])
    recipe = get_recipe_by_source(source, recipe_index)
    chat_id = call.message.chat.id

    if chat_id not in user_favorites:
        user_favorites[chat_id] = set()
    user_favorites[chat_id].add(recipe['name'])

    bot.answer_callback_query(
        call.id,
        text=f"❤️ «{recipe['name']}» added to favorites!",
        show_alert=True
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    fav_btn = types.InlineKeyboardButton("💔 Remove from Favorites", callback_data=f"unfav_{source}_{recipe_index}")
    shop_btn = types.InlineKeyboardButton("🛒 Shopping List", callback_data=f"shop_{source}_{recipe_index}")
    rating = user_ratings.get(chat_id, {}).get(recipe['name'])
    rating_str = f" {'⭐' * rating}" if rating else ""
    rate_btn = types.InlineKeyboardButton(f"⭐ Rate{rating_str}", callback_data=f"rate_{source}_{recipe_index}")
    markup.add(fav_btn)
    markup.row(shop_btn, rate_btn)
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    except Exception:
        pass


# ========================
# FAVORITES — REMOVE
# ========================
@bot.callback_query_handler(func=lambda call: call.data.startswith('unfav_'))
def handle_remove_favorite(call):
    parts = call.data.split('_')
    source = parts[1]
    recipe_index = int(parts[2])
    recipe = get_recipe_by_source(source, recipe_index)
    chat_id = call.message.chat.id

    if chat_id in user_favorites:
        user_favorites[chat_id].discard(recipe['name'])

    bot.answer_callback_query(
        call.id,
        text=f"💔 «{recipe['name']}» removed from favorites",
        show_alert=True
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    fav_btn = types.InlineKeyboardButton("❤️ Add to Favorites", callback_data=f"fav_{source}_{recipe_index}")
    shop_btn = types.InlineKeyboardButton("🛒 Shopping List", callback_data=f"shop_{source}_{recipe_index}")
    rating = user_ratings.get(chat_id, {}).get(recipe['name'])
    rating_str = f" {'⭐' * rating}" if rating else ""
    rate_btn = types.InlineKeyboardButton(f"⭐ Rate{rating_str}", callback_data=f"rate_{source}_{recipe_index}")
    timer_btn = types.InlineKeyboardButton("⏳ Set Timer", callback_data=f"timer_{source}_{recipe_index}")
    markup.add(fav_btn)
    markup.row(shop_btn, rate_btn)
    markup.add(timer_btn)
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    except Exception:
        pass


# ========================
# RATING — SHOW BUTTONS
# ========================
@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_'))
def handle_rate(call):
    parts = call.data.split('_')
    source = parts[1]
    recipe_index = int(parts[2])
    recipe = get_recipe_by_source(source, recipe_index)
    bot.answer_callback_query(call.id)

    markup = types.InlineKeyboardMarkup(row_width=5)
    stars = [types.InlineKeyboardButton(
        f"{'⭐' * i}", callback_data=f"setrate_{source}_{recipe_index}_{i}"
    ) for i in range(1, 6)]
    markup.add(*stars)

    bot.send_message(
        call.message.chat.id,
        f"⭐ Rate the recipe *{recipe['name']}*:",
        parse_mode='Markdown',
        reply_markup=markup
    )


# ========================
# RATING — SAVE
# ========================
@bot.callback_query_handler(func=lambda call: call.data.startswith('setrate_'))
def handle_set_rate(call):
    parts = call.data.split('_')
    source = parts[1]
    recipe_index = int(parts[2])
    stars = int(parts[3])
    recipe = get_recipe_by_source(source, recipe_index)
    chat_id = call.message.chat.id

    if chat_id not in user_ratings:
        user_ratings[chat_id] = {}
    user_ratings[chat_id][recipe['name']] = stars

    bot.answer_callback_query(
        call.id,
        text=f"{'⭐' * stars} Rating {stars}/5 saved for «{recipe['name']}»!",
        show_alert=True
    )

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass


# ========================
# TIMER
# ========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("timer_"))
def recipe_timer(call):
    parts = call.data.split("_")
    source = parts[1]
    recipe_index = parts[2]

    recipe = get_recipe_by_source(source, recipe_index)
    minutes = extract_minutes(recipe)
    total_seconds = int(minutes * 60)

    if total_seconds < 60:
        bot.answer_callback_query(call.id, f"⏳ Timer set for {total_seconds} seconds!")
    else:
        bot.answer_callback_query(call.id, f"⏳ Timer set for {int(minutes)} min!")

    def countdown():
        try:
            mins_disp = total_seconds // 60
            secs_disp = total_seconds % 60
            timer_message = bot.send_message(
                call.message.chat.id,
                f"⏳ Time left: {mins_disp:02d}:{secs_disp:02d}"
            )

            for remaining in range(total_seconds, 0, -1):
                mins = remaining // 60
                secs = remaining % 60
                try:
                    bot.edit_message_text(
                        f"⏳ Time left: {mins:02d}:{secs:02d}" if total_seconds >= 60 else f"⏳ Time left: {remaining} sec",
                        call.message.chat.id,
                        timer_message.message_id
                    )
                except Exception:
                    pass
                time.sleep(1)

            bot.send_message(
                call.message.chat.id,
                f"🔔 Timer for «{recipe['name']}» is done! Bon appétit! 🍽"
            )
        except Exception as e:
            print(f"Timer error: {e}")

    threading.Thread(target=countdown, daemon=True).start()


# ========================
# VIEW FAVORITES
# ========================
@bot.message_handler(func=lambda m: m.text == "❤️ Favorites")
def show_favorites(message):
    chat_id = message.chat.id
    favs = user_favorites.get(chat_id, set())

    if not favs:
        bot.send_message(chat_id, "💔 You have no favorite recipes yet.\n\nFind a recipe and tap ❤️ Add to Favorites!", reply_markup=main_menu())
        return

    text = "❤️ *Your Favorite Recipes:*\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)

    for name in favs:
        found = None
        source = 'main'
        idx = 0
        for i, r in enumerate(RECIPES):
            if r['name'] == name:
                found = r
                idx = i
                source = 'main'
                break
        if not found:
            for i, r in enumerate(BAKING_RECIPES):
                if r['name'] == name:
                    found = r
                    idx = i
                    source = 'bake'
                    break
        if found:
            rating = user_ratings.get(chat_id, {}).get(name)
            stars = f" {'⭐' * rating}" if rating else ""
            text += f"• {name}{stars}\n"
            markup.add(types.InlineKeyboardButton(
                f"🍽 {name}", callback_data=f"favrecipe_{source}_{idx}"
            ))

    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)


# ========================
# MY RATINGS
# ========================
@bot.message_handler(func=lambda m: m.text == "⭐ My Ratings")
def show_my_ratings(message):
    chat_id = message.chat.id
    ratings = user_ratings.get(chat_id, {})

    if not ratings:
        bot.send_message(chat_id, "⭐ You haven't rated any recipes yet.\n\nOpen any recipe and tap ⭐ Rate!", reply_markup=main_menu())
        return

    text = "⭐ *Your Recipe Ratings:*\n\n"
    for name, stars in sorted(ratings.items(), key=lambda x: -x[1]):
        text += f"{'⭐' * stars} {name}\n"

    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=main_menu())


# ========================
# MY RECIPES (user-added)
# ========================
@bot.message_handler(func=lambda m: m.text == "📚 My Recipes")
def my_recipes(message):
    user_recipes = UserRecipe.objects.filter(user_id=message.from_user.id)

    if not user_recipes:
        bot.send_message(message.chat.id, "📭 You have no saved recipes yet.", reply_markup=main_menu())
        return

    text = "📚 *Your Recipes:*\n\n"
    for recipe in user_recipes:
        text += f"🍽 {recipe.name}\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu())


# ========================
# ADD RECIPE
# ========================
@bot.message_handler(func=lambda m: m.text == "➕ Add Recipe")
@bot.message_handler(commands=['add'])
def add_recipe_start(message):
    user_states[message.chat.id] = {'step': 'add_name'}
    bot.send_message(message.chat.id, "➕ *Add a Recipe*\n\nEnter the recipe name:", parse_mode='Markdown')


def handle_add_recipe(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if not isinstance(state, dict):
        return False

    step = state.get('step')
    text = message.text.strip() if message.text else ""

    if step == 'add_name':
        # Validate: name must not be empty
        if not text:
            bot.send_message(chat_id, "⚠️ Recipe name cannot be empty. Please enter the recipe name:")
            return True
        if len(text) > 100:
            bot.send_message(chat_id, "⚠️ Name is too long (max 100 characters). Please shorten it:")
            return True
        state['name'] = text
        state['step'] = 'add_ingredients'
        bot.send_message(chat_id, "📦 Enter the ingredients (comma-separated):\n_Example: chicken, garlic, cream_", parse_mode='Markdown')

    elif step == 'add_ingredients':
        # Validate: ingredients must not be empty
        if not text:
            bot.send_message(chat_id, "⚠️ Ingredients cannot be empty. Enter at least one ingredient:")
            return True
        state['ingredients'] = text
        state['step'] = 'add_kbju'
        bot.send_message(chat_id, "🔢 Enter nutrition per 100g:\n_Example: 450 kcal / P 20 / F 15 / C 40_\n\nNo data? Type *0*", parse_mode='Markdown')

    elif step == 'add_kbju':
        # Any non-empty value accepted; numbers are extracted later (defaults to 0 if none found)
        if not text:
            bot.send_message(chat_id, "⚠️ Please enter nutrition info or type *0* to skip:", parse_mode='Markdown')
            return True
        state['kbju'] = text
        state['step'] = 'add_time'
        bot.send_message(chat_id, "⏱ Enter cooking time:\n_Example: 20 min_", parse_mode='Markdown')

    elif step == 'add_time':
        # Validate: cooking time must not be empty
        if not text:
            bot.send_message(chat_id, "⚠️ Cooking time cannot be empty.\n_Example: 20 min_", parse_mode='Markdown')
            return True
        state['time'] = text
        state['step'] = 'add_text'
        bot.send_message(chat_id, "📝 Enter the recipe (cooking steps):")

    elif step == 'add_text':
        # Validate: recipe steps must not be empty
        if not text:
            bot.send_message(chat_id, "⚠️ Recipe steps cannot be empty. Please describe the cooking process:")
            return True
        state['recipe_text'] = text

        kbju = state.get('kbju', '')
        nums = re.findall(r'\d+', kbju)
        cal = int(nums[0]) if len(nums) > 0 else 0
        prot = float(nums[1]) if len(nums) > 1 else 0
        fat = float(nums[2]) if len(nums) > 2 else 0
        carb = float(nums[3]) if len(nums) > 3 else 0

        try:
            UserRecipe.objects.create(
                user_id=message.from_user.id,
                name=state['name'],
                ingredients=state['ingredients'],
                calories=cal,
                proteins=prot,
                fats=fat,
                carbs=carb,
                cooking_time=state['time'],
                recipe_text=state['recipe_text'],
            )
            bot.send_message(
                chat_id,
                f"✅ *Recipe «{state['name']}» added!*\n\n"
                f"🔢 Nutrition: {state['kbju']}\n\n"
                "Now you can write ingredients and I'll find recipes.",
                parse_mode='Markdown',
                reply_markup=main_menu()
            )
        except Exception as e:
            bot.send_message(chat_id, f"❌ Save error: {e}\n\nPlease try again or contact support.", reply_markup=main_menu())

        user_states[chat_id] = 'waiting_products'

    return True


# ========================
# MENU BUTTON HANDLERS
# ========================
@bot.message_handler(func=lambda m: m.text in ["🍳 Recipes", "📅 Plan", "ℹ️ About"])
def handle_menu_buttons(message):
    text = message.text
    if text == "📅 Plan":
        weekly_plan(message)
    elif text == "ℹ️ About":
        about(message)
    elif text == "🍳 Recipes":
        bot.send_message(
            message.chat.id,
            f"🍳 *All Recipes ({len(RECIPES)} total)*\n\nWrite the ingredients you have at home separated by commas, and I'll find matching recipes!\n\n_Example: chicken, rice, carrot_",
            parse_mode='Markdown',
            reply_markup=main_menu()
        )


# ========================
# SHOPPING BUTTON
# ========================
@bot.message_handler(func=lambda m: m.text == "🛒 Shopping")
def handle_shopping_button(message):
    bot.send_message(
        message.chat.id,
        "🛒 Open a recipe and tap *Shopping List* to get the ingredients list!",
        parse_mode='Markdown',
        reply_markup=main_menu()
    )


# ========================
# NON-TEXT MESSAGE HANDLERS
# ========================
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    bot.send_message(
        message.chat.id,
        "🎤 *Voice messages are not supported.*\n\nPlease type the ingredients as text:\n_Example: chicken, rice, garlic_",
        parse_mode='Markdown',
        reply_markup=main_menu()
    )

@bot.message_handler(content_types=['video_note'])
def handle_video_note(message):
    bot.send_message(
        message.chat.id,
        "🎥 *Video circles are not supported.*\n\nPlease type the ingredients as text:\n_Example: egg, milk, cheese_",
        parse_mode='Markdown',
        reply_markup=main_menu()
    )

@bot.message_handler(content_types=['sticker'])
def handle_sticker(message):
    bot.send_message(
        message.chat.id,
        "😄 Nice sticker! But I only understand text.\n\nWrite the ingredients you have:\n_Example: pasta, tomato, garlic_",
        parse_mode='Markdown',
        reply_markup=main_menu()
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.send_message(
        message.chat.id,
        "📷 *Photos are not supported.*\n\nPlease type the ingredients as text:\n_Example: chicken, garlic, cream_",
        parse_mode='Markdown',
        reply_markup=main_menu()
    )

@bot.message_handler(content_types=['document', 'video', 'audio', 'animation'])
def handle_other_media(message):
    bot.send_message(
        message.chat.id,
        "📎 *I only work with text.*\n\nWrite the ingredients you have:\n_Example: egg, butter, flour_",
        parse_mode='Markdown',
        reply_markup=main_menu()
    )


# ========================
# MAIN TEXT HANDLER
# ========================
@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id

    # Guard: ignore non-text messages (stickers, voice, etc.)
    if not message.text:
        bot.send_message(
            chat_id,
            "⚠️ Please send a text message with ingredients.\n_Example: chicken, rice, garlic_",
            parse_mode='Markdown',
            reply_markup=main_menu()
        )
        return

    text = message.text.strip()

    # Guard: ignore empty or whitespace-only input
    if not text:
        bot.send_message(
            chat_id,
            "⚠️ You sent an empty message.\n\nPlease write the ingredients you have, separated by commas:\n_Example: egg, milk, cheese_",
            parse_mode='Markdown',
            reply_markup=main_menu()
        )
        return

    # Add recipe flow
    if handle_add_recipe(message):
        return

    # Search recipes
    groups, total_keywords, keywords = find_recipes_smart(text)
    bake_groups, _, _ = find_recipes_smart(text, BAKING_RECIPES)

    if not groups and not bake_groups:
        response_text = (
            f"😔 No recipes found for *{text}*.\n\n"
            "💡 *Try writing differently*, for example:\n"
            "• chicken, rice, carrot\n"
            "• egg, milk, flour\n"
            "• pasta, tomato, garlic\n\n"
            f"📚 Database has {len(ALL_RECIPES)} recipes!"
        )
        bot.send_message(chat_id, response_text, parse_mode='Markdown', reply_markup=main_menu())
        save_to_db(message, response_text)
        return

    response_text = "🔍 *Found recipes matching your ingredients!*\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    buttons_added = set()

    if groups:
        max_score = max(groups.keys())
        for score in sorted(groups.keys(), reverse=True):
            if score < max_score - 2:
                break
            recipes_in_group = groups[score]
            if score == max_score and score == total_keywords:
                response_text += "✅ *All ingredients match:*\n"
            elif score == max_score:
                response_text += f"✅ *Best matches ({score} of {total_keywords}):*\n"
            else:
                response_text += f"\n🟡 *Almost matches ({score} of {total_keywords}):*\n"
            for r in recipes_in_group:
                ing_list = ", ".join(r['ingredients'])
                response_text += f"• {r['name']}\n  _needs: {ing_list}_\n"

    if bake_groups:
        max_bake = max(bake_groups.keys())
        response_text += "\n🎂 *Baking recipes:*\n"
        for score in sorted(bake_groups.keys(), reverse=True):
            if score < max_bake - 1:
                break
            for r in bake_groups[score]:
                response_text += f"• {r['name']}\n"

    response_text += "\n👇 *Tap on a recipe you want to cook:*"

    if groups:
        max_score = max(groups.keys())
        for score in sorted(groups.keys(), reverse=True):
            if score < max_score - 2:
                break
            for recipe in groups[score]:
                name = recipe['name']
                if name not in buttons_added:
                    idx = RECIPES.index(recipe)
                    markup.add(types.InlineKeyboardButton(
                        text=f"🍽 {name} ({recipe['time']})",
                        callback_data=f"recipe_{idx}"
                    ))
                    buttons_added.add(name)

    if bake_groups:
        max_bake = max(bake_groups.keys())
        for score in sorted(bake_groups.keys(), reverse=True):
            if score < max_bake - 1:
                break
            for recipe in bake_groups[score]:
                name = recipe['name']
                if name not in buttons_added:
                    idx = BAKING_RECIPES.index(recipe)
                    markup.add(types.InlineKeyboardButton(
                        text=f"🎂 {name} ({recipe['time']})",
                        callback_data=f"bake_{idx}"
                    ))
                    buttons_added.add(name)

    bot.send_message(chat_id, response_text, parse_mode='Markdown', reply_markup=markup)
    save_to_db(message, response_text)


print("✅ Bot is running!")
bot.infinity_polling()