import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from database import get_user, save_user
from config import (
    choose_allergies,
    choose_diet,
    allergy_keyboard,
    diet_keyboard,
)

logger = logging.getLogger(__name__)


async def cmd_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /setup flow — loads existing profile so user can see what's saved."""
    user_id = update.effective_user.id
    profile = get_user(user_id)

    context.user_data["temp_allergies"] = list(profile.get("allergies", []))
    context.user_data["temp_diets"] = list(profile.get("diets", []))

    current = (
        ", ".join(profile["allergies"]) if profile["allergies"] else "none saved yet"
    )

    kb = ReplyKeyboardMarkup(allergy_keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"*Step 1 of 2 — Allergies*\n\n"
        f"Tap allergens to add/remove them.\n\n"
        f"Current: _{current}_\n\n"
        f"When finished tap *Done*.",
        reply_markup=kb,
        parse_mode="Markdown",
    )

    return choose_allergies


async def handle_allergy_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called each time user taps an allergy button. Toggles on/off. Done → diet step."""
    text = update.message.text.strip()

    if text.lower() == "no allergies":
        context.user_data["temp_allergies"] = []
        kb = ReplyKeyboardMarkup(diet_keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "✅ Got it — no allergies.\n\n"
            "*Step 2 of 2 — Diet preferences*\n"
            "Tap diets to add/remove them.\n\n"
            "When finished tap *Done*.",
            reply_markup=kb,
            parse_mode="Markdown",
            )
        return choose_diet

    if text.lower() == "done":
        selected = context.user_data.get("temp_allergies", [])
        current = ", ".join(selected) if selected else "none"

        kb = ReplyKeyboardMarkup(diet_keyboard, resize_keyboard=True)

        await update.message.reply_text(
            f"✅ Allergies saved.\n\n"
            f"Current allergies: _{current}_\n\n"
            f"*Step 2 of 2 — Diet preferences*\n"
            f"Tap diets to add/remove them.\n\n"
            f"When finished tap *Done*.",
            reply_markup=kb,
            parse_mode="Markdown",
        )
        return choose_diet

    allergy = text.lower()
    temp = context.user_data.get("temp_allergies", [])

    if allergy in temp:
        temp.remove(allergy)
        action = f"Removed _{allergy}_"
    else:
        temp.append(allergy)
        action = f"Added _{allergy}_"

    context.user_data["temp_allergies"] = temp
    current = ", ".join(temp) if temp else "none selected"

    await update.message.reply_text(
        f"{action}\n\nCurrent: *{current}*",
        parse_mode="Markdown",
    )
    return choose_allergies


async def handle_diet_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called each time user taps a diet button. Toggles on/off. Done → save & end."""
    text = update.message.text.strip()

    if text.lower() == "done":
        user_id = update.effective_user.id
        allergies = context.user_data.get("temp_allergies", [])
        diets = context.user_data.get("temp_diets", [])
        username = update.effective_user.username or ""

        save_user(user_id, allergies, diets, username)
        logger.info(f"Saved profile for user {user_id}: allergies={allergies}, diets={diets}")

        await update.message.reply_text(
            f"✅ *Profile Saved!*\n\n"
            f"🚫 Allergies: _{', '.join(allergies) if allergies else 'none'}_\n"
            f"🥗 Diets: _{', '.join(diets) if diets else 'none'}_\n\n"
            f"Now send me any dish name to check it.\n"
            f"Or try /menu to scan a full restaurant menu.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    diet = text.lower()
    temp = context.user_data.get("temp_diets", [])

    if diet in temp:
        temp.remove(diet)
        action = f"Removed _{diet}_"
    else:
        temp.append(diet)
        action = f"Added _{diet}_"

    context.user_data["temp_diets"] = temp
    current = ", ".join(temp) if temp else "none selected"

    await update.message.reply_text(
        f"{action}\n\nCurrent: *{current}*",
        parse_mode="Markdown",
    )
    return choose_diet
