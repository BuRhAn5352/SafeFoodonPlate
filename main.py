import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from config import telegram_token, choose_allergies, choose_diet
from database import init_db

# Import all handlers
from handlers.setup import cmd_setup, handle_allergy_choice, handle_diet_choice
from handlers.dish_check import check_dish
from handlers.menu_scan import cmd_menu, handle_menu_text
from handlers.suggestions import cmd_suggest, handle_suggest_text
from handlers.feedback import handle_feedback_button, handle_feedback_note

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def cmd_start(update, context):
    name = update.effective_user.first_name or "there"
    await update.message.reply_text(
        f"👋 Hey {name}! Welcome to *SafePlate*.\n\n"
        "I check if dishes are safe for your allergies and diet.\n\n"
        "*First, set up your profile:*\n"
        "/setup — takes 30 seconds\n\n"
        "🍽 *Then use me like this:*\n"
        "• Send any dish name → _Is Butter Chicken safe?_\n"
        "• /menu → paste a full restaurant menu\n"
        "• /suggest → get safe dish ideas for a cuisine\n\n"
        "/help → see all commands",
        parse_mode="Markdown",
    )


async def cmd_help(update, context):
    await update.message.reply_text(
        "📋 *SafePlate Commands*\n\n"
        "/setup   → Set your allergies and diet preferences\n"
        "/profile → View your saved profile\n"
        "/menu    → Scan a full restaurant menu\n"
        "/suggest → Get safe dish suggestions by cuisine\n"
        "/help    → This message\n\n"
        "Or just send any dish name:\n"
        "_Is Paneer Tikka safe?_\n"
        "_Chicken Satay_\n"
        "_Can I eat Pad Thai?_",
        parse_mode="Markdown",
    )


async def cmd_profile(update, context):
    from database import get_user

    user_id = update.effective_user.id
    profile = get_user(user_id)
    allergies = profile.get("allergies", [])
    diets = profile.get("diets", [])

    if not allergies and not diets:
        await update.message.reply_text(
            "No profile saved yet.\nUse /setup to create one — it takes 30 seconds."
        )
        return

    await update.message.reply_text(
        f"👤 *Your SafePlate Profile*\n\n"
        f"🚫 Allergies: _{', '.join(allergies) if allergies else 'none'}_\n"
        f"🥗 Diet:      _{', '.join(diets) if diets else 'none'}_\n\n"
        "Use /setup to update.",
        parse_mode="Markdown",
    )


async def route_text(update, context):
    """
    All plain text messages land here.
    Routes to the right handler based on what we're waiting for.
    """
    if context.user_data.get("awaiting_feedback_note"):
        await handle_feedback_note(update, context)
        return

    if context.user_data.get("awaiting_menu"):
        await handle_menu_text(update, context)
        return

    if context.user_data.get("awaiting_suggest"):
        await handle_suggest_text(update, context)
        return

    # Default: treat as a dish check
    await check_dish(update, context)


def main():
    init_db()

    app = Application.builder().token(telegram_token).build()

    # /setup multi-step conversation
    setup_conversation = ConversationHandler(
        entry_points=[CommandHandler("setup", cmd_setup)],
        states={
            choose_allergies: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_allergy_choice)
            ],
            choose_diet: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_diet_choice)
            ],
        },
        fallbacks=[
            CommandHandler("start", cmd_start),
            CommandHandler("help", cmd_help),
        ],
        per_message=False,
    )

    # 1. Conversation handler first (highest priority)
    app.add_handler(setup_conversation)

    # 2. Command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("profile", cmd_profile))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("suggest", cmd_suggest))

    # 3. Inline button callbacks (feedback)
    app.add_handler(CallbackQueryHandler(handle_feedback_button, pattern="^fb_"))

    # 4. Text fallback — MUST be last
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_text))

    logger.info("SafePlate bot started.")
    print("\n✅ SafePlate is running. Press Ctrl+C to stop.\n")
    app.run_polling()


if __name__ == "__main__":
    main()
