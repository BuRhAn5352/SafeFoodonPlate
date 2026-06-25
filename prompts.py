##all the prompts to be saved here to train 
from config import diet_rule

def build_diet_context(diets: list) -> str:

    """
    converts user's selected diets into detailed rules for the model
    E.g. : ["jain", "diabetic"] toh pura full text explanation of both will come
    """

    if not diets:
        return "no specific diet preference"
    
    rules =[]

    for diet in diets:
        rule = diet_rule.get(diet.lower())

        if rule:
            rules.append(f"{diet.upper()}: {rule}")

        else:
            rules.append(f"{diet.upper()}: follow standard guidelines for this diet")
    
    return "\n".join(rules)


def dish_prompts(dish: str,allergies: str,diets: list) -> str:

    allergy_str= ", ".join(allergies) if allergies else "none"
    diet_context = build_diet_context(diets)

    return f""" You are SafeFoodonPlate, a food safety assistant specialising in Indian food.

    USER ALLERGIES : {allergy_str}
    USER DIET RULES : {diet_context}
    DISH TO ANALYZE : "{dish}"

    Think carefully about:

    1. ALLERGENS (obvious + hidden):
    - Satay, chikki, groundnut chutney    → peanuts
    - Naan, paratha, most curries          → dairy (ghee, butter, cream)
    - Most Indian restaurant base gravies  → cashew paste (tree nuts)
    - Fried items                          → shared frying oil (cross-contamination)
    - Caesar dressing, some chutneys       → eggs / fish
    - Pad Thai, some Chinese dishes        → peanuts + eggs + soy
    - Gulab Jamun, Kheer, Rasgulla         → milk solids (dairy)
    - Biryani                              → may have fried onions + nut garnish

    2. JAIN DIET (if selected):
    - No onion, no garlic — most Indian curries have both in the base
    - No root vegetables: aloo (potato), gajar (carrot), mooli (radish)
    - No meat, eggs, fish
    - Many dishes labelled "veg" are still NOT Jain — check carefully
    - Common Jain-safe: plain dal, rice, fruit, certain dry sabzis
    
    3. STATUS RULES:
    - DANGER = definitely violates allergy or diet
    - WARN   = may violate depending on preparation, or cross-contamination risk
    - SAFE   = no allergens AND fits all diet rules
    
    Reply ONLY as valid JSON, no markdown, no extra text outside JSON:
    {{
        "status" : "DANGER",
        "allergens" : ["dairy", "tree nuts"],
        "diet_issue" : "Not Jain — contains onion and garlic in the gravy",
        "reason" : "One clear sentence about the main risk.",
        "tip" : "One actionable thing to ask the restaurant.",
        "safe_alternatives" : ["Dish 1", "Dish 2"]
    }}
    If no allergen issue → set allergens to [].
    If no diet issue    → set diet_issue to null.
    If no alternatives  → set safe_alternatives to [].
    """

def menu_prompt(menu_text:str, allergies: list, diets: list) -> str:


        allergy_str = ", ".join(allergies) if allergies else None
        diet_context = build_diet_context(diets)

        return f"""
        You are SafeFoodonPlate, a food safety assistant specialising in Indian food.
        USER ALLERGIES : {allergy_str}
        USER DIET RULES : {diet_context}
        
        The user pasted a restaurant menu below. Extract every dish name and analyze each one.
        Key hidden allergen reminders:
        - Indian restaurant gravies almost always have onion + garlic (important for Jain users)
        - Most paneer dishes have dairy
        - Biryani often has fried onions + nut garnish
        - Any dish with "makhani", "malai", "cream" → dairy
        - Any dish with "groundnut", "satay", "chikki" → peanuts
        - Root vegetables (aloo, gajar, arbi, shakarkandi) → not Jain
        
        MENU : {menu_text}
        
        Return a JSON array — one object per dish found:
        [
        {{"dish": "Paneer Butter Masala", "status": "DANGER", "reason": "Contains dairy (paneer + butter + cream)."}},
        {{"dish": "Dal Tadka",            "status": "WARN",   "reason": "Usually safe but may have ghee — confirm with restaurant."}},
        {{"dish": "Jeera Rice",           "status": "SAFE",   "reason": "Plain rice with cumin — no allergens."}}
        ]

        STATUS RULES:
        - DANGER = definitely violates allergy or diet
        - WARN   = may violate depending on preparation
        - SAFE   = no allergens, fits all diet rules
        
        Reply ONLY as a valid JSON array. No markdown. No text outside the array.
        """


def suggest_prompts(cuisine:str, allergies: list, diets:list) -> str:
     
     allergy_str = ", ".join(allergies) if allergies else None
     diet_context = build_diet_context(diets)
     
     return f"""
     You are SafeFoodonPlate, a food safety assistant specialising in Indian food.

     USER ALLERGIES : {allergy_str}
     USER DIET RULES : {diet_context}
     CUISINE / RESTAURANT TYPE: "{cuisine}"
     
     Suggest exactly 5 dishes this user can safely eat.
     Explain briefly WHY each dish is safe for their specific allergies and diet.
     For Jain users only suggest dishes with no onion, no garlic, no root vegetables, no meat.
     Reply ONLY as a valid JSON array:
     [
     {{
        "dish": "Dal Dhokli",
        "reason": "Made with wheat and dal — no onion/garlic if requested Jain style. No allergens.",
        "calories": "approx 280 kcal"
        }}
    ]
        No markdown. No text outside the array.
        """
 



