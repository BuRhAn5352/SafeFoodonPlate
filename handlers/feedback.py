import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import save_feedback, update_feedback_note

logger = logging.getLogger(__name__)


async def handle_feedback_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called when user taps 👍 Correct or 👎 Wrong button.
    Parses callback data, saves to database.
    If wrong — asks for a brief note (optional).
    """
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data  # format: "fb_correct|dish name|STATUS"

    await query.answer()  # removes loading spinner

    parts = data.split("|")
    action = parts[0]                           # fb_correct or fb_wrong
    dish = parts[1] if len(parts) > 1 else "unknown"
    status = parts[2] if len(parts) > 2 else "unknown"

    # Remove buttons so user can't tap twice
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    if action == "fb_correct":
        save_feedback(user_id, dish, status, correct=1, note="")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="👍 Thanks! This helps make SafePlate smarter.",
        )
        logger.info(f"Feedback CORRECT from user {user_id} for '{dish}'")

    elif action == "fb_wrong":
        save_feedback(user_id, dish, status, correct=0, note="")

        context.user_data["feedback_dish"] = dish
        context.user_data["feedback_status"] = status
        context.user_data["awaiting_feedback_note"] = True

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                "👎 Sorry about that!\n\n"
                "What was wrong? _(Optional — type a note or send /skip)_"
            ),
            parse_mode="Markdown",
        )
        logger.info(f"Feedback WRONG from user {user_id} for '{dish}'")


async def handle_feedback_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Called when user types a note after tapping 👎 Wrong.
    Saves the note, then clears the waiting flag.
    """
    user_id = update.effective_user.id

    # Guard: no message text
    if not update.message or not update.message.text:
        if update.message:
            await update.message.reply_text("Please send text or /skip.")
        return

    note = update.message.text.strip()

    # User can send /skip to skip the note
    if note.lower() == "/skip":
        note = ""

    dish = context.user_data.get("feedback_dish", "")

    if dish:
        update_feedback_note(user_id, dish, note)

    # Clear the waiting state
    context.user_data["awaiting_feedback_note"] = False
    context.user_data["feedback_dish"] = ""
    context.user_data["feedback_status"] = ""

    await update.message.reply_text(
        "✅ Feedback saved — thank you! This helps improve SafePlate."
    )
    logger.info(f"Feedback note saved for user {user_id}: '{note[:50]}'")
