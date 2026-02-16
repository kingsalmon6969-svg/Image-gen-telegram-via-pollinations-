import telebot
import requests
import os
import random
from telebot import types
from flask import Flask
from threading import Thread

# 1. SETUP CREDENTIALS
BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_KEY = os.environ.get('POLLINATIONS_KEY')

if not BOT_TOKEN or not API_KEY:
    # On Render, we set these in the Environment Variables dashboard
    print("Warning: Credentials not found (Check Environment Variables)")

bot = telebot.TeleBot(BOT_TOKEN)

# --- KEEP ALIVE SERVER START ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive! 🌸"

def run_http():
    # Render assigns a port automatically in the PORT env var
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_http)
    t.start()
# --- KEEP ALIVE SERVER END ---

# 2. CONFIGURATION
MODELS = {
    'Flux': 'flux',
    'Imagen 4': 'imagen-4',
    'Klein (HD)': 'klein',
    'Z-Image (Turbo)': 'zimage'
}

user_data = {}

# 3. HANDLERS
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in MODELS.keys()]
    markup.add(*buttons)
    
    bot.send_message(
        message.chat.id, 
        "🌸 <b>HERMAX AI is Awake!</b> 🌸\n\n"
        "Hi there! Let's paint some dreams together! 🎨✨\n\n"
        "🌈 <b>Pick your magic wand (model) below to start:</b>",
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text in MODELS.keys())
def set_model(message):
    selected_name = message.text
    user_data[message.chat.id] = MODELS[selected_name]
    
    bot.reply_to(
        message, 
        f"💖 <b>Yay! Model set to:</b> {selected_name} ✨\n"
        "🌟 Now, simply type your idea to create a masterpiece!",
        parse_mode='HTML',
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: True)
def handle_prompt(message):
    chat_id = message.chat.id
    prompt = message.text
    
    # Default to 'flux' if no model selected
    model = user_data.get(chat_id, 'flux')
    
    msg = bot.reply_to(message, "🖍️ <b>Mixing the colors...</b> 🎨\n<i>Dreaming up your image with " + model + "... please wait! 💖</i>", parse_mode='HTML')
    
    try:
        seed = random.randint(0, 2147483647)
        url = f"https://gen.pollinations.ai/image/{prompt}"
        
        params = {
            "model": model,
            "seed": seed,
            "width": 1024,
            "height": 1024,
            "nologo": "true"
        }
        
        headers = {
            "Authorization": f"Bearer {API_KEY}"
        }

        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            bot.send_photo(chat_id, response.content, caption=f"✨ <b>Here is your art!</b> ✨\n\n🍭 <b>Prompt:</b> {prompt}\n🎀 <b>Style:</b> {model}\n\n<i>Hope you love it!</i> 🥰", parse_mode='HTML')
            bot.delete_message(chat_id, msg.message_id) 
        else:
            bot.edit_message_text(f"😿 <b>Oh no!</b> The magic fizzled out (Error: {response.status_code})", chat_id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"💔 <b>Oops!</b> Something went wrong: {str(e)}", chat_id, msg.message_id)

# 5. RUN
if __name__ == "__main__":
    print("Bot is blooming... 🌸")
    keep_alive()  # Start the web server
    bot.infinity_polling() # Start the bot
