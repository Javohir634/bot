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
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

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

async
