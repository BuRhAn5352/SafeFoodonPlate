from dotenv import load_dotenv
import os

load_dotenv('credentials.env')

#all the keys and app wide contents live here
telegram_token = os.getenv("telegram_tkn")
groq_key = os.getenv("groq_apikey")

groq_model = "llama-3.3-70b-versatile"

DB_file="safeplate.db"

choose_allergies = 1
choose_diet = 2

# common allergens shown as tap buttons during /setup

allergy_keyboard = [
    ["Peanuts", "Dairy", "Gluten"],
    ["Eggs", "Soy", "Shellfish"],
    ["Fish", "Tree Nuts", "Onion/Garlic"],
    ["No Allergies","Done"]
]

#diet and lifestyle accordance

diet_keyboard = [
    ["jain","vegeterian","vegan"],
    ["low calorie","high protein", "diabetic"],
    ["low sodium", "no spicy", "no preference"],
    ["Done"]
]

#this dictionary is passed into prompts so Claude knows
#exactly what rules to apply for each diet

diet_rule = {

    "jain":(
        "Strict jain diet: no meat,no fish, no eggs, no onion, no garlic,"
        "no root vegetables (potato, carrot, beetroot, radish, turnip),"
        "no eating after sunset (not checkable), no multi-layered vegetables like cauliflower."
        "Many Indian restaurant dishes contain onion/garlic in the base gravy so flag these as WARN or DANGER."
    ),

    "vegetarian": (
        "Vegetarian (Indian style): no meat, no fish, no eggs."
        "Dairy is allowed. Check for hidden meat in gravies, stocks, and sauces."
    ),

    "vegan": (
        "Vegan: no meat, no fish, no eggs, no dairy (milk, cream, butter, ghee, paneer, curd). "
        "Most Indian curries use ghee or cream — flag these carefully."
    ),

    "low calorie": (
        "Low calorie diet: flag dishes that are deep fried, made with heavy cream,"
        "lots of ghee/butter, or are high-sugar desserts."
        "Prefer grilled, steamed, or dal-based dishes."
    ),

    "diabetic": (
        "Diabetic diet: avoid high glycemic foods such as white rice, maida (refined flour),"
        "sugary desserts, fruit juices, biryani in large portions."
        "Flag mithai, gulab jamun, jalebi, halwa as DANGER"
        "Prefer whole grains, dal, sabzi."
    ),

    "high protein": (
        "High protein diet: prefer dal, paneer, chicken, eggs, fish, sprouts, soya. "
        "Flag dishes that are mostly carbs with no protein as WARN."
    ),

    "low sodium": (
        "Low sodium diet: flag pickles (achar), papad, processed foods,"
        "restaurant curries (generally high salt), canned items as WARN or DANGER"
    ),

    "no spicy": (
        "No spicy food: flag dishes known to be very spicy"
        "vindaloo, chettinad, kolhapuri, schezwan, very red curries"
        "Suggest mild alternatives where possible."
    ),
}

