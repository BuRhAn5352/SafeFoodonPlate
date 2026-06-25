import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_user
from prompts import suggest_prompts
from model import call_groq, parse_json, format_suggest_reply

logger = logging.getLogger(__name__)


async def cmd_suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: User sends /suggest → ask what cuisine they're ordering from."""
    user_id = update.effective_user.id
    profile = get_user(user_id)

    if not profile["allergies"] and not profile["diets"]:
        await update.message.reply_text(
            "Please set up your allergy profile first.\nUse /setup — it takes 30 seconds."
        )
        return

    context.user_data["awaiting_suggest"] = True

    await update.message.reply_text(
        "🍽 *What can I eat?*\n\n"
        "Tell me the cuisine or restaurant type in your *next message*.\n\n"
        "Examples:\n"
        "• _North Indian_\n"
        "• _Chinese_\n"
        "• _South Indian_\n"
        "• _Italian pizza place_\n"
        "• _McDonald's_",
        parse_mode="Markdown",
    )


async def handle_suggest_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: User tells the cuisine → ask Groq for 5 safe dishes."""
    user_id = update.effective_user.id
    cuisine = update.message.text.strip()
    profile = get_user(user_id)

    context.user_data["awaiting_suggest"] = False

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    prompt = suggest_prompts(cuisine, profile["allergies"], profile["diets"])

    try:
        raw = call_groq(prompt, max_tokens=800)
        parsed = parse_json(raw)

        if isinstance(parsed, list) and parsed:
            reply = format_suggest_reply(parsed)
        else:
            reply = (
                "Couldn't find suggestions for that.\n"
                "Try a different cuisine name — like _North Indian_ or _Chinese_."
            )

        await update.message.reply_text(reply, parse_mode="Markdown")
        logger.info(f"Suggestions for user {user_id}: cuisine='{cuisine}'")

    except Exception as e:
        logger.error(f"Suggest error: {e}")
        await update.message.reply_text("Something went wrong. Please try again.")
