# 🍳 RecipebotMA — Telegram Cooking Assistant

A Telegram bot that helps you find recipes based on ingredients you have at home.

---

## 📋 Description

The bot can:

- Search recipes by ingredients you type (40+ recipes)
- Show full recipe cards with step-by-step instructions and nutrition info per 100g
- Save favourite recipes
- Rate recipes (1–5 stars)
- Add your own custom recipes
- Generate a random weekly meal plan
- Show a shopping list for any recipe
- Save all queries via Django admin panel

---

## 🛠 Technologies

| Layer | Stack |
|---|---|
| Bot | pyTelegramBotAPI |
| Admin / ORM | Django 5.x |
| Environment variables | python-dotenv |
| Language | Python 3.10+ |
| Database | SQLite |

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourname/ramen_bot.git
cd ramen_bot
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file in the project root

```env
BOT_TOKEN=your_token_from_BotFather
DJANGO_SETTINGS_MODULE=admin_panel.settings
SECRET_KEY=your_django_secret_key
DEBUG=True
```

### 5. Apply Django migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

---

## 🚀 Running the Bot

```bash
# Terminal 1 — bot
python recipe_bot/tg_bot.py

# Terminal 2 — Django admin (optional)
python manage.py runserver
```

Django admin is available at: `http://127.0.0.1:8000/admin/`

> ⚠️ Run only **one bot instance** at a time, otherwise you will get a 409 Conflict error.

---

## 💬 Usage Examples

Type ingredients separated by commas:

```
egg, milk, cheese
chicken, rice, soy sauce
pasta, tomato, garlic
```

The bot will reply with a list of matching recipes and buttons to open each one.

---

## 📱 Bot Commands

| Command | Action |
|---|---|
| `/start` | Welcome message and main menu |
| `/help` | Usage instructions |
| `/plan` | Generate a random weekly meal plan |
| `/about` | Bot info and stats |
| `/add` | Start adding your own recipe |

## 🔘 Menu Buttons

| Button | Action |
|---|---|
| 🍳 Recipes | All recipes and search tip |
| 📚 My Recipes | Recipes added by the user |
| ❤️ Favorites | Saved favourite recipes |
| ⭐ My Ratings | All rated recipes |
| 🛒 Shopping | Shopping list from a recipe |
| 📅 Plan | Weekly meal plan |
| ➕ Add Recipe | Add a custom recipe |
| ℹ️ About | Bot description and stats |

---

## 🛡 Error Handling

### Empty input
If the user sends an empty message, the bot asks to write ingredients with an example.

### Unknown product / no recipe found
```
😔 No recipes found for "xyz".
💡 Try writing differently, for example:
• chicken, rice, carrot
• egg, milk, flour
• pasta, tomato, garlic
```

### Voice messages
```
🎤 Voice messages are not supported.
Please type the ingredients as text.
Example: chicken, rice, garlic
```

### Video circles (video note)
```
🎥 Video circles are not supported.
Please type the ingredients as text.
Example: egg, milk, cheese
```

### Stickers
```
😄 Nice sticker! But I only understand text.
Write the ingredients you have.
```

### Photos and files
```
📷 Photos are not supported.
Please type the ingredients as text.
```

### Invalid input when adding a recipe
- Empty name → bot asks to enter the name again
- Empty ingredients → bot asks to enter ingredients again
- Empty nutrition info → bot asks to enter or type `0` to skip
- Empty cooking time → bot asks to enter again with an example
- Empty recipe steps → bot asks to describe the cooking process
- Database error → bot shows a clear error message

---

## 🗂 Project Structure

```
ramen_bot/
├── recipe_bot/
│   ├── tg_bot.py           ← main bot file
│   ├── models.py           ← UserQuery, UserRecipe models
│   ├── admin.py
│   └── migrations/
├── admin_panel/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── .env                    ← token and settings (do not commit!)
├── manage.py
├── requirements.txt
└── README.md
```

---

## 📸 Screenshots

| Start | Recipe search | Recipe card |
|---|---|---|
| ![start](screenshots/start.png) | ![search](screenshots/search.png) | ![card](screenshots/card.png) |

---

## 📄 License

MIT — free to use and modify.
