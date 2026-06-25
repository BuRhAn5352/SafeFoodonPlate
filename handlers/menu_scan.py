import logging
from telegram.constants import ChatAction
from telegram import Update
from telegram.ext import ContextTypes
from database import get_user
from prompts import menu_prompt
from model import call_groq, parse_json, format_menu_reply

logger = logging.getLogger(__name__)


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: User sends /menu → ask them to paste the menu text next."""
    user_id = update.effective_user.id
    profile = get_user(user_id)

    if not profile["allergies"] and not profile["diets"]:
        await update.message.reply_text(
            "Please set up your allergy profile first.\nUse /setup — it takes 30 seconds."
        )
        return

    context.user_data["awaiting_menu"] = True

    await update.message.reply_text(
        "*Menu Scan Mode*\n\n"
        "Paste the full restaurant menu text in your *next message*.\n\n"
        "I'll scan every dish and flag what's safe for you.\n\n"
        "Tip: Copy menu text from Swiggy or Zomato and paste it here.",
        parse_mode="Markdown",
    )


async def handle_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: User pastes the menu → send to Groq, return flagged dish list."""
    user_id = update.effective_user.id
    menu_text = update.message.text
    profile = get_user(user_id)

    context.user_data["awaiting_menu"] = False

    await update.message.reply_text("🔍 Scanning your menu... give me a few seconds.")
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    prompt = menu_prompt(menu_text, profile["allergies"], profile["diets"])

    try:
        raw = call_groq(prompt, max_tokens=1500)
        parsed = parse_json(raw)

        if isinstance(parsed, list) and parsed:
            reply = format_menu_reply(parsed)
        else:
            reply = (
                "Couldn't read that menu properly.\n\n"
                "Try pasting it again — ideally one dish per line."
            )

        await update.message.reply_text(reply, parse_mode="Markdown")
        logger.info(
            f"Menu scan for user {user_id}: {len(parsed) if isinstance(parsed, list) else 0} dishes found."
        )

    except Exception as e:
        logger.error(f"Menu scan error: {e}")
        await update.message.reply_text(
            "Something went wrong scanning the menu. Please try again."
        )
