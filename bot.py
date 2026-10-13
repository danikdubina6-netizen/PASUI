import asyncio
import os
import sys
import time
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

groq_client = Groq(api_key=GROQ_API_KEY)
print("Groq API клиент успешно инициализирован!")

START_TIME = time.time()
MAX_UPTIME = 4.5 * 3600 

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Отправь мне голосовое, кружочек или аудио, и я выдам чистый текст."
    )

@dp.message(F.voice | F.video_note | F.audio)
async def handle_audio(message: types.Message):
    if time.time() - START_TIME > MAX_UPTIME:
        await message.reply("Плановая перезагрузка. Секунду, скоро буду на связи.")
        sys.exit(0)

    status_msg = await message.answer("Расшифровываю...")
    
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
        with open(input_file, "rb") as audio_file:
            transcript = groq_client.audio.transcriptions.create(
                file=(input_file, audio_file.read()),
                model="whisper-large-v3",
                language="ru",
                temperature=0.0,
                response_format="text"
            )
        
        text = str(transcript).strip()

        # Тотальный экстерминатус Димы Торзока во всех падежах и вариациях
        garbage_phrases = [
            "dimatorzok", "диматорзок", "дима торзок", 
            "субтитры сделал", "субтитры создавал", 
            "продолжение следует", "савский трек"
        ]
        
        text_lower = text.lower()
        if any(garbage in text_lower for garbage in garbage_phrases):
            if len(text.split()) < 8:
                text = ""
            else:
                for g in garbage_phrases:
                    text = text.replace(g, "").replace(g.capitalize(), "").strip()

        if text:
            await message.reply(text)
        else:
            await message.reply("Не удалось разобрать слова. Запись пустая.")
    except Exception as e:
        await message.reply(f"Ошибка при обработке: {e}")
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
        
