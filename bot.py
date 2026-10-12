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

print("Загрузка быстрой модели Whisper (large-v3)...")
whisper_model = WhisperModel("large-v3", device="cpu", compute_type="int8")
print("Модель успешно загружена!")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Отправь мне голосовое или аудио, и я выведу текст."
    )

@dp.message(F.voice | F.video_note | F.audio)
async def handle_audio(message: types.Message):
    status_msg = await message.answer("Секунду, расшифровываю...")
    
    if message.voice:
        file_id = message.voice.file_id
    elif message.video_note:
        file_id = message.video_note.file_id
    else:
        file_id = message.audio.file_id

    file = await bot.get_file(file_id)
    
    input_file = f"temp_{message.from_user.id}.ogg"
    await bot.download_file(file.file_path, input_file)
    
    try:
        segments, info = whisper_model.transcribe(
            input_file,
            beam_size=5,
            temperature=0.0,
            language="ru",
            vad_filter=True,  # Включаем фильтр тишины, чтобы мусор и шумы не превращались в галлюцинации
            vad_parameters=dict(min_silence_duration_ms=500),
            initial_prompt="Разговорная речь на русском языке."
        )
        
        text = " ".join([segment.text for segment in segments]).strip()
        
        # Отсекаем известные мусорные галлюцинации модели на пустых местах
        garbage_phrases = ["тысячелетиями копал я", "dimatorzok", "субтитры"]
        if any(g in text.lower() for g in garbage_phrases) or len(text) < 2:
            text = ""

        if text:
            await message.reply(text)
        else:
            await message.reply("Не удалось разобрать слова (слишком тихо или пустой звук).")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        await status_msg.delete()

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
