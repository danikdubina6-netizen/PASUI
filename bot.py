import asyncio
import os
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from faster_whisper import WhisperModel

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    sys.exit("Ошибка: Переменная BOT_TOKEN не найдена!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Используем продвинутую модель 'medium' для максимальной точности
print("Загрузка мощной модели Whisper (medium)...")
whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")
print("Модель успешно загружена!")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **Привет! Я продвинутый расшифрователь голосовых и видеокружочков.**\n\n"
        "Просто отправь мне любое голосовое сообщение или видеозаметку, и я переведу их в текст максимально точно!"
    )

@dp.message(F.voice | F.video_note)
async def handle_audio(message: types.Message):
    status_msg = await message.answer("🎧 Внимательно слушаю и расшифровываю...")
    
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    file = await bot.get_file(file_id)
    
    input_file = f"temp_{message.from_user.id}.ogg"
    await bot.download_file(file.file_path, input_file)
    
    try:
        segments, _ = whisper_model.transcribe(
            input_file,
            beam_size=5,
            best_of=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            initial_prompt="Точная расшифровка разговорной речи на русском языке без галлюцинаций."
        )
        
        text = " ".join([segment.text for segment in segments]).strip()
        
        if text:
            await message.reply(f"📜 **Расшифровка:**\n\n{text}")
        else:
            await message.reply("⚠️ Не удалось разобрать слова. Возможно, запись слишком тихая или шумная.")
    except Exception as e:
        await message.reply(f"❌ Ошибка при обработке: {e}")
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        await status_msg.delete()

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
