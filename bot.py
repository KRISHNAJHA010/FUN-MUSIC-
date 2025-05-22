
import logging
from aiogram import Bot, Dispatcher, executor, types
from yt_dlp import YoutubeDL
import asyncio
import json
import os

API_TOKEN = os.getenv("API_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

if not os.path.exists("playlists.json"):
    with open("playlists.json", "w") as f:
        json.dump({}, f)

def load_playlists():
    with open("playlists.json", "r") as f:
        return json.load(f)

def save_playlists(data):
    with open("playlists.json", "w") as f:
        json.dump(data, f)

AUTO_DELETE_ENABLED = True
AUTO_DELETE_TIME = 60  # seconds

ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'nocheckcertificate': True,
    'outtmpl': '%(title)s.%(ext)s',
    'noplaylist': True,
}

async def auto_delete_message(message: types.Message):
    if AUTO_DELETE_ENABLED:
        await asyncio.sleep(AUTO_DELETE_TIME)
        try:
            await message.delete()
        except:
            pass

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("Welcome to the YouTube Music Bot! Send a YouTube link or search keyword.")

@dp.message_handler(commands=['myplaylist'])
async def my_playlist(message: types.Message):
    data = load_playlists()
    user_id = str(message.from_user.id)
    playlist = data.get(user_id, [])
    if not playlist:
        await message.reply("Your playlist is empty.")
    else:
        text = "Your Playlist:\n"
for i, item in enumerate(playlist):
    text += f"{i+1}. {item['title']}\n"
await message.reply(text)

@dp.message_handler()
async def handle_query(message: types.Message):
    query = message.text
    search_msg = await message.reply("Searching...")
    with YoutubeDL({"quiet": True}) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        except:
            await search_msg.edit_text("No results found.")
            return

    title = info.get("title")
    url = info.get("webpage_url")
    thumb = info.get("thumbnail")

    buttons = [
        [
            types.InlineKeyboardButton("MP3 - 128kbps", callback_data=f"mp3|{url}"),
            types.InlineKeyboardButton("MP3 - 320kbps", callback_data=f"mp3_320|{url}")
        ],
        [
            types.InlineKeyboardButton("720p", callback_data=f"720p|{url}"),
            types.InlineKeyboardButton("1080p", callback_data=f"1080p|{url}")
        ],
        [
            types.InlineKeyboardButton("➕ Add to Playlist", callback_data=f"add|{url}|{title}")
        ]
    ]

    thumb_msg = await bot.send_photo(
    chat_id=message.chat.id,
    photo=thumb,
    caption=f"""🎵 <b>{title}</b>\n🔗 <a href='{url}'>Watch on YouTube</a>""",
    parse_mode="HTML",
    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons)
)
)
    await auto_delete_message(thumb_msg)
    await search_msg.delete()

@dp.callback_query_handler()
async def callback_handler(call: types.CallbackQuery):
    action = call.data.split("|")[0]
    if action == "add":
        _, url, title = call.data.split("|", 2)
        data = load_playlists()
        user_id = str(call.from_user.id)
        if user_id not in data:
            data[user_id] = []
        data[user_id].append({"title": title, "url": url})
        save_playlists(data)
        await call.answer("Added to your playlist.", show_alert=True)
    else:
        await call.answer("Downloading...")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
