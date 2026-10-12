import asyncio
import os
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from funasr import AutoModel

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    sys.exit("Ошибка: Переменная BOT_TOKEN не найдена!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

print("Загрузка продвинутой модели SenseVoiceSmall...")
# Загружаем модель SenseVoice, которая идеально понимает живую речь и сленг
model = AutoModel(
    model="iic/SenseVoiceSmall",
    device="cpu",
    disable_update=True
)
print("Модель успешно загружена!")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я твой ИИ-расшифрователь на современной модели SenseVoice.\n\n"
        "Отправь мне аудио, и я выдам чистый текст без ошибок!"
    )

@dp.message(F.voice | F.video_note | F.audio)
async def handle_audio(message: types.Message):
    status_msg = await message.answer("Слушаю и расшифровываю...")
    
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
        # Генерация расшифровки через SenseVoice
        res = model.generate(
            input=input_file,
            language="auto",
            use_itn=True,
        )
        
        text = ""
        if res and len(res) > 0:
            text = res[0].get("text", "").strip()
            
        # Убираем возможные теги эмоций модели, если они появятся (например <|RU|>)
        for tag in ["<|RU|>", "<|EN|>", "<|ZH|>", "<|Speech|>", "<|Applause|>", "<|BGM|>"]:
            text = text.replace(tag, "")
        text = text.strip()

        if text:
            await message.reply(text)
        else:
            await message.reply("Не удалось разобрать слова. Запись пустая или слишком тихая.")
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
    
