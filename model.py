import json
import logging
from groq import Groq
from config import groq_key, groq_model

logger = logging.getLogger(__name__)
client = Groq(api_key=groq_key)

#first we will call groq
def call_groq(prompt:str, max_tokens:int = 800) -> str:
    """
    sends a prompt to groq and returns the raw text response
    fucntion is still called cal_goq o no other file needs to change
    max_tokens controls how long the reply can be 
    """
    response = client.chat.completions.create(
        model=groq_model,
        max_tokens=max_tokens,
        messages=[
            {
                "role":"system",
                "content":(
                    "you are SafeFoodonPlate, a food safety assistant."
                    "you always reply ONLY with valid JSON (no markdown),"
                    "no explanation, no backticks. Just the raw JSON."
                )
            },
            {
                "role" : "user",
                "content":prompt
            }
        ]
    )
    return response.choices[0].message.content.strip()


def parse_json(raw: str) -> dict | list | None:
    """
    safely parses groq's json response.
    handles cases wheere the model adds eextra text around the Json.
    returns none if parsing fails completely
    """
    #try drect parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    #try extractinf JSON block if model added ectra text
    try:
        if "{" in raw:
            s = raw.find("{")
            e = raw.rfind("}") + 1
            return json.loads(raw[s:e])
        
        if "[" in raw:
            s = raw.find("[")
            e = raw.rfind("]") + 1
            return json.loads(raw[s:e])
        
    except json.JSONDecodeError:
        pass


    logger.warning(f"could not pprase response as JSON:\n{raw[:300]}")
    return None


# format replies

def format_dish_reply( parsed: dict, dish : str) -> str:
    """
    turns the dish check json into a readable telegram message"
    """
    icons = {"SAFE": "✅", "WARN": "⚠️", "DANGER": "❌"}
    labels = {"SAFE": "SAFE TO EAT", "WARN": "CHECK FIRST",
               "DANGER": "AVOID THIS"}
    
    status = parsed.get("status","WARN")
    icon = icons.get(status,"⚠️")
    label = labels.get(status, "CHECK FIRST")

    lines =[
        f"{icon} *{label}*",
        f"_{dish}_"
        "",
        parsed.get("reason","No reason provided")
    ]

    if parsed.get("diet_issue"):
        lines.append(f"diet issues:* {parsed['diet_issue']}")

    if parsed.get("tip") and status != "SAFE":
        lines.append(f"\n {parsed['tip']}")
 
    if parsed.get("safe_alternatives"):
        alts = ", ".join(parsed["safe_alternatives"])
        lines.append(f"\n🍽 *Try instead:* {alts}")

    lines.append(
        "\n\n_⚠️ SafeFoodonPlate reduces risk always confirm with the restaurant for severe allergies._"
    )
    return "\n".join(lines)

def format_menu_reply(items: list) -> str:
    """
    Turns the menu scan JSON array into a grouped Telegram message.
    Groups dishes into DANGER / WARN / SAFE sections.

    """
    if not items:
        return "Couldn't read that menu. Try again with clear text."
    
    icons = {"SAFE":  "✅", "WARN": "⚠️", "DANGER": "❌"}
    safe,warn,danger = [],[],[]

    for item in items:
        s = item.get("status","WARN")
        line = f"{icons[s]} * {item['dish']}*\n  _{item.get('reason', '')}_"

        if   s == "SAFE":   safe.append(line)
        elif s == "WARN":   warn.append(line)
        else:               danger.append(line)

    parts = []

    if danger:
        parts.append("❌ *AVOID THESE*\n\n" + "\n\n".join(danger))
    if warn:
        parts.append("⚠️ *CHECK FIRST*\n\n" + "\n\n".join(warn))
    if safe:
        parts.append("✅ *SAFE TO EAT*\n\n" + "\n\n".join(safe))
 
    parts.append("_⚠️ Always confirm with the restaurant for severe allergies._")
    return "\n\n──────────\n\n".join(parts)
 
 
def format_suggest_reply(items: list) -> str:
    """
    Turns the suggestions JSON array into a readable Telegram message.
    """
    if not items:
        return "Couldn't find suggestions. Try a different cuisine name."
 
    lines = ["✅ *Safe dishes you can try:*", ""]
    for i, item in enumerate(items, 1):
        lines.append(f"*{i}. {item['dish']}*")
        lines.append(f"   {item.get('reason', '')}")
        if item.get("calories"):
            lines.append(f"   🔥 {item['calories']}")
        lines.append("")
 
    lines.append("_⚠️ Always confirm with the restaurant for severe allergies._")
    return "\n".join(lines)

 
 

    


