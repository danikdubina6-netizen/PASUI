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

# Загружаем топовую модель large-v3
print("Загрузка топовой модели Whisper (large-v3)...")
whisper_model = WhisperModel("large-v3", device="cpu", compute_type="int8")
print("Модель успешно загружена!")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я твой продвинутый расшифрователь голосовых и видеокружочков.\n\n"
        "Отправь мне аудио, и я сначала объясню суть сказанного, а ниже выдам точную расшифровку!"
    )

@dp.message(F.voice | F.video_note)
async def handle_audio(message: types.Message):
    status_msg = await message.answer("Слушаю и анализирую...")
    
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    file = await bot.get_file(file_id)
    
    input_file = f"temp_{message.from_user.id}.ogg"
    await bot.download_file(file.file_path, input_file)
    
    try:
        segments, _ = whisper_model.transcribe(
            input_file,
            beam_size=5,
            best_of=5,
            language="ru",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
            initial_prompt="Точная расшифровка русской разговорной речи, сленга и мата без цензуры."
        )
        
        text = " ".join([segment.text for segment in segments]).strip()
        
        if text:
            # Простейший мини-анализ темы на основе текста сообщения
            summary = "Коротко о сути: человек делится мыслями, эмоциями или обсуждает текущие дела."
            if len(text) > 40:
                summary = f"О чем речь: обсуждение темы, связанной со словами «{text[:35]}...»"
            
            response_text = (
                f"🧠 {summary}\n\n"
                f"📜 Точная расшифровка:\n{text}"
            )
            await message.reply(response_text)
        else:
            await message.reply("Не удалось разобрать слова. Возможно, запись пустая или слишком тихая.")
    except Exception as e:
        await message.reply(f"Ошибка при обработке: {e}")
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        await status_msg.delete()

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
