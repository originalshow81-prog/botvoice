import os
import subprocess
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salut! Sunt botul tău de audio.\n\n"
        "Trimite-mi un mesaj vocal sau un fișier audio și îți elimin pauzele automat. 🎙️\n\n"
        "Funcționează cu: vocale Telegram, MP3, WAV, OGG, M4A."
    )


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message.voice:
        tg_file_obj = message.voice
        ext = "ogg"
    elif message.audio:
        tg_file_obj = message.audio
        ext = "mp3"
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("audio"):
        tg_file_obj = message.document
        ext = "ogg"
    else:
        return

    processing_msg = await message.reply_text("⏳ Procesez fișierul, o secundă...")

    input_path = f"/tmp/input_{message.message_id}.{ext}"
    output_path = f"/tmp/output_{message.message_id}.mp3"

    try:
        tg_file = await context.bot.get_file(tg_file_obj.file_id)
        await tg_file.download_to_drive(input_path)

        filtru = (
            "silenceremove="
            "start_periods=1:start_silence=0.3:start_threshold=-40dB:"
            "stop_periods=-1:stop_silence=0.3:stop_threshold=-40dB"
        )

        result = subprocess.run(
            ["ffmpeg", "-i", input_path, "-af", filtru, output_path, "-y"],
            capture_output=True
        )

        await processing_msg.delete()

        if result.returncode == 0:
            with open(output_path, "rb") as f:
                await message.reply_audio(audio=f, title="Audio fara pauze")
        else:
            await message.reply_text("❌ Eroare la procesare. Încearcă cu alt fișier.")

    except Exception as e:
        logger.error(f"Eroare: {e}")
        await message.reply_text("❌ Ceva nu a mers. Încearcă din nou.")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.VOICE | filters.AUDIO | filters.Document.AUDIO,
        handle_audio
    ))
    app.run_polling()


if __name__ == "__main__":
    main()
