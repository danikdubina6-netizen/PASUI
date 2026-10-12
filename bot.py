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

# Загружаем ультрасовременную модель SenseVoiceSmall
print("Загрузка современной модели SenseVoice...")
model = AutoModel(
    model="iic/SenseVoiceSmall",
    device="cpu",
    disable_update=True
)
print("Модель успешно загружена!")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я твой продвинутый ИИ-расшифрователь голосовых и видеокружочков.\n\n"
        "Отправь мне любое голосовое или кружочек, и я переведу его в текст без ошибок и галлюцинаций!"
    )

@dp.message(F.voice | F.video_note)
async def handle_audio(message: types.Message):
    status_msg = await message.answer("Слушаю и расшифровываю...")
    
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    file = await bot.get_file(file_id)
    
    input_file = f"temp_{message.from_user.id}.ogg"
    await bot.download_file(file.file_path, input_file)
    
    try:
        # Распознаем речь с помощью SenseVoice
        res = model.generate(
            input=input_file,
            language="auto", # Автоматически определяет язык (отлично понимает русский)
            use_itn=True,    # Нормализация текста (красивые цифры, знаки)
        )
        
        text = ""
        if res and len(res) > 0:
            text = res[0].get("text", "").strip()
        
        if text:
            await message.reply(f"Расшифровка:\n\n{text}")
        else:
            await message.reply("Не удалось разобрать слова. Возможно, запись слишком тихая.")
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
    
