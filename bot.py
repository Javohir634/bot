import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update, Message
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

DATA_FILE = Path("channels.json")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def load_channels() -> set[str]:
    if not DATA_FILE.exists():
        return set()
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return set(data.get("channels", []))
    except Exception:
        return set()

def save_channels(channels: set[str]) -> None:
    DATA_FILE.write_text(
        json.dumps({"channels": list(channels)}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

def is_owner(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == OWNER_ID

async def owner_only(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_owner(update):
        await update.message.reply_text("⛔ This bot is private.")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only(update, context):
        return

    text = (
        "🤖 *Channel Forwarder Bot*\n\n"
        "I will forward every new post from channels where I am admin.\n\n"
        "*Commands:*\n"
        "/add `<channel>` – add channel to monitor\n"
        "/remove `<channel>` – stop monitoring\n"
        "/list – show monitored channels\n"
        "/status – bot status\n\n"
        "Example:\n"
        "`/add @mychannel`\n"
        "`/add -1001234567890`"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only(update, context):
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n`/add @channelusername`\nor\n`/add -100xxxxxxxxxx`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    channel = context.args[0].strip()
    channels = load_channels()

    if channel in channels:
        await update.message.reply_text("Already monitoring this channel.")
        return

    channels.add(channel)
    save_channels(channels)
    await update.message.reply_text(f"✅ Now monitoring: `{channel}`", parse_mode=ParseMode.MARKDOWN)

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only(update, context):
        return

    if not context.args:
        await update.message.reply_text("Usage: `/remove @channel` or `/remove -100...`", parse_mode=ParseMode.MARKDOWN)
        return

    channel = context.args[0].strip()
    channels = load_channels()

    if channel not in channels:
        await update.message.reply_text("This channel is not in the list.")
        return

    channels.remove(channel)
    save_channels(channels)
    await update.message.reply_text(f"🗑 Removed: `{channel}`", parse_mode=ParseMode.MARKDOWN)

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only(update, context):
        return

    channels = load_channels()
    if not channels:
        await update.message.reply_text("No channels are being monitored yet.\nUse /add")
        return

    text = "*Currently monitoring:*\n\n" + "\n".join(f"• `{c}`" for c in sorted(channels))
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only(update, context):
        return

    channels = load_channels()
    await update.message.reply_text(
        f"🤖 Bot is running\n📡 Monitoring *{len(channels)}* channel(s)",
        parse_mode=ParseMode.MARKDOWN,
    )

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message: Message = update.channel_post
    if not message:
        return

    chat = message.chat
    channels = load_channels()

    identifiers = set()
    if chat.username:
        identifiers.add(f"@{chat.username}")
    identifiers.add(str(chat.id))

    if not identifiers & channels:
        return

    try:
        await context.bot.forward_message(
            chat_id=OWNER_ID,
            from_chat_id=chat.id,
            message_id=message.message_id,
        )
        logger.info(f"Forwarded post from {chat.title or chat.id}")
    except Exception as e:
        logger.error(f"Failed to forward: {e}")

async def handle_edited_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.edited_channel_post
    if not message:
        return

    chat = message.chat
    channels = load_channels()

    identifiers = set()
    if chat.username:
        identifiers.add(f"@{chat.username}")
    identifiers.add(str(chat.id))

    if not identifiers & channels:
        return

    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"✏️ Post was edited in *{chat.title or chat.id}*",
            parse_mode=ParseMode.MARKDOWN,
        )
        await context.bot.forward_message(
            chat_id=OWNER_ID,
            from_chat_id=chat.id,
            message_id=message.message_id,
        )
    except Exception as e:
        logger.error(f"Failed to handle edit: {e}")

async def private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_owner(update):
        return
    await update.message.reply_text("This is a private forwarder bot.")

def main():
    if not BOT_TOKEN or not OWNER_ID:
        raise RuntimeError("BOT_TOKEN and OWNER_ID must be set")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_channel))
    app.add_handler(CommandHandler("remove", remove_channel))
    app.add_handler(CommandHandler("list", list_channels))
    app.add_handler(CommandHandler("status", status))

    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, handle_channel_post))
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_CHANNEL_POST, handle_edited_channel_post))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, private_message))

    logger.info("Bot started...")
    app.run_polling(allowed_updates=["channel_post", "edited_channel_post", "message"])

if __name__ == "__main__":
    main()