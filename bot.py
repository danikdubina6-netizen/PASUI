import asyncio
import os
import sys
import uuid
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from faster_whisper import WhisperModel

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    sys.exit("Ошибка: Переменная BOT_TOKEN не найдена!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

print("Загрузка продвинутой модели Whisper Large V3 Turbo...")
# Используем state-of-the-art модель: высокая скорость и максимальная точность без лишних слоев
whisper_model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
print("Модель успешно загружена!")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Отправь голосовое, и я расшифрую его на турбо-модели.")

@dp.message(F.voice | F.video_note | F.audio)
async def handle_audio(message: types.Message):
    status_msg = await message.answer("Слушаю...")
    
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
        segments, _ = whisper_model.transcribe(
            input_file,
            beam_size=5,
            best_of=5,
            temperature=0.0,
            language="ru",
            vad_filter=True,  # С turbo-моделью фильтр работает идеально и не режет нужные слова
            vad_parameters=dict(
                min_silence_duration_ms=200,
                speech_pad_ms=200
            )
        )
        
        text = " ".join([segment.text for segment in segments]).strip()
        
        garbage_phrases = ["савский трек", "тысячелетиями копал", "dimatorzok", "субтитры"]
        if any(g in text.lower() for g in garbage_phrases):
            text = ""

        if text:
            await message.reply(text)
        else:
            await message.reply("Не удалось разобрать слова.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        try:
            await status_msg.delete()
        except:
            pass

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
