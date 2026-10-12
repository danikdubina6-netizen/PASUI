import asyncio
import os
import sys
from aiogram import Bot, Dispatcher, F, types
from faster_whisper import WhisperModel

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    sys.exit("Ошибка: Переменная BOT_TOKEN не найдена!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Используем модель 'small' — она в разы точнее 'tiny', отлично понимает русский и украинский
print("Загрузка продвинутой модели Whisper...")
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
print("Продвинутая модель успешно загружена!")

@dp.message(F.voice | F.video_note)
async def handle_audio(message: types.Message):
    status_msg = await message.answer("🎧 Слушаю и расшифровываю...")
    
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    file = await bot.get_file(file_id)
    
    input_file = f"temp_{message.from_user.id}.ogg"
    await bot.download_file(file.file_path, input_file)
    
    try:
        # Передаем initial_prompt, чтобы Whisper не галлюцинировал иероглифами на тишине/помехах
        segments, info = whisper_model.transcribe(
            input_file,
            beam_size=5,
            best_of=5,
            vad_filter=True, # Включаем фильтр тишины и шумов
            vad_parameters=dict(min_silence_duration_ms=500),
            initial_prompt="Расшифровка голосового сообщения на русском или украинском языке."
        )
        
        text = " ".join([segment.text for segment in segments]).strip()
        
        if text:
            await message.reply(f"📜 **Расшифровка:**\n\n{text}")
        else:
            await message.reply("⚠️ Не удалось разобрать слова (тишина или слишком сильный шум).")
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
    
