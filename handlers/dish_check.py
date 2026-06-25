import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from prompts import dish_prompts
from database import get_user
from model import parse_json, call_groq, format_dish_reply

logger = logging.getLogger(__name__)


async def check_dish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main dish check handler — takes any dish name and returns SAFE/WARN/DANGER."""
    user_id = update.effective_user.id
    dish = update.message.text.strip()

    profile = get_user(user_id)
    allergies = profile["allergies"]
    diets = profile["diets"]

    if not allergies and not diets:
        await update.message.reply_text(
            "⚠️ Please set up your profile first — it takes 30 seconds.\n\n"
            "Use /setup and select your allergies.\n"
            "If you have none, tap *No Allergies* then *Done*.",
            parse_mode="Markdown"
            )
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    prompt = dish_prompts(dish, allergies, diets)

    try:
        raw = call_groq(prompt, max_tokens=400)
        parsed = parse_json(raw)

        if not parsed or not isinstance(parsed, dict):
            await update.message.reply_text(
                "Couldn't analyze that dish.\n\n"
                "Try:\n"
                "• Butter Chicken\n"
                "• Paneer Tikka\n"
                "• Is Butter Chicken safe?"
            )
            return

        dish_status = parsed.get("status", "unknown")
        reply = format_dish_reply(parsed, dish)

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "👍 Correct",
                        callback_data=f"fb_correct|{dish}|{dish_status}",
                    ),
                    InlineKeyboardButton(
                        "👎 Wrong",
                        callback_data=f"fb_wrong|{dish}|{dish_status}",
                    ),
                ]
            ]
        )

        await update.message.reply_text(
            reply, parse_mode="Markdown", reply_markup=keyboard
        )
        logger.info(f"Dish check for user {user_id}: '{dish}' → {dish_status}")

    except Exception as e:
        logger.error(f"Dish check error for '{dish}': {e}")
        await update.message.reply_text(
            "Something went wrong checking that dish. Please try again!"
        )
