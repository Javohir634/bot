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
    app.run_polling(
        allowed_updates=["channel_post", "edited_channel_post", "message"],
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
