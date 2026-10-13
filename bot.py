import asyncio
import os
import sys
import uuid
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    sys.exit("Ошибка: Переменная BOT_TOKEN не найдена!")
if not GROQ_API_KEY:
    sys.exit("Ошибка: Переменная GROQ_API_KEY не найдена!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализируем клиента Groq для работы с облачным Whisper
groq_client = Groq(api_key=GROQ_API_KEY)
print("Groq API клиент успешно инициализирован!")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Бот работает на сверхбыстром Groq API (Whisper Large V3). "
        "Отправь голосовое или аудио, и я выдам точный текст!"
    )

@dp.message(F.voice | F.video_note | F.audio)
async def handle_audio(message: types.Message):
    status_msg = await message.answer("Молниеносная расшифровка через Groq...")
    
    if message.voice:
        file_id = message.voice.file_id
    elif message.video_note:
        file_id = message.video_note.file_id
    else:
        file_id = message.audio.file_id

    file = await bot.get_file(file_id)
    
    unique_suffix = uuid.uuid4().hex[:8]
    input_file = f"temp_{message.from_user.id}_{unique_suffix}.ogg"
    
    await bot.download_file(file.file_path, input_file)
    
    try:
        # Отправляем аудиофайл в Groq API для мгновенной транскрипции
        with open(input_file, "rb") as audio_file:
            transcript = groq_client.audio.transcriptions.create(
                file=(input_file, audio_file.read()),
                model="whisper-large-v3",  # Или "whisper-large-v3-turbo"
                language="ru",
                temperature=0.0,
                response_format="text"
            )
        
        text = str(transcript).strip()

        if text:
            await message.reply(text)
        else:
            await message.reply("Не удалось разобрать слова. Запись пустая.")
    except Exception as e:
        await message.reply(f"Ошибка при обращении к Groq API: {e}")
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        try:
            await status_msg.delete()
        except:
            pass

async def main():
    print("Бот запущен и готов принимать аудио!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
