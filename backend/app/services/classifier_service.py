"""
C.O.V.E.R.T - Report Classifier Service

Keyword-based classification of civic reports into department categories,
plus Bangalore locality detection.
"""

from typing import List, Dict, Optional


# ── Category keywords ───────────────────────────────────────────────────────

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "roads": [
        "pothole", "road", "footpath", "pavement", "crater", "broken road",
        "divider", "flyover", "underpass", "junction", "road repair",
        "road damage", "speed breaker",
    ],
    "waste": [
        "garbage", "waste", "trash", "dump", "litter", "sanitation",
        "sweeping", "dustbin", "compost", "swachh", "rubbish",
        "open dumping", "burning waste",
    ],
    "water": [
        "water", "pipe burst", "leakage", "sewage", "drainage", "borewell",
        "tanker", "water supply", "overflow", "flooding", "bwssb",
        "no water", "dirty water", "water cut",
    ],
    "electricity": [
        "electricity", "power cut", "streetlight",
        "light not working", "transformer", "bescom",
        "electric pole", "power outage", "sparking wire",
        "no power", "short circuit",
    ],
    "pollution": [
        "pollution", "smoke", "dust", "air quality", "smell", "odour",
        "factory", "industrial", "chemical", "effluent",
        "noise pollution", "loud music", "burning garbage", "kspcb",
    ],
    "corruption": [
        "bribe", "corruption", "officer demanded", "demanded money",
        "illegal payment", "misconduct", "misuse of power",
        "fraud", "lokayukta", "scam",
    ],
    "food_safety": [
        "food", "restaurant", "hotel", "adulteration", "expired food",
        "food hygiene", "cockroach", "unhygienic", "fssai",
        "food poisoning", "stale food",
    ],
    "construction": [
        "illegal construction", "building violation",
        "unauthorized building", "heritage building",
        "demolition", "bbmp notice", "construction without permission",
    ],
    "public_health": [
        "hospital", "clinic", "disease outbreak", "epidemic",
        "mosquito breeding", "dengue", "malaria", "rat infestation",
        "pest", "stagnant water", "open defecation",
    ],
    "traffic": [
        "traffic jam", "signal broken", "no signal", "rash driving",
        "wrong side", "illegal parking", "accident",
        "footpath parking", "traffic police",
    ],
    "law_order": [
        "harassment", "noise complaint", "loud party",
        "drunk and disorderly", "fight", "theft",
        "chain snatching", "eve teasing", "stalking", "threat",
    ],
}


# ── Bangalore locality identifiers ──────────────────────────────────────────

BANGALORE_IDENTIFIERS: List[str] = [
    "bangalore", "bengaluru", "bbmp", "bwssb", "bescom", "kspcb", "lokayukta",
    "koramangala", "indiranagar", "whitefield", "jayanagar", "jp nagar",
    "electronic city", "hebbal", "yelahanka", "marathahalli", "btm layout",
    "hsr layout", "bannerghatta", "rajajinagar", "malleswaram", "basavanagudi",
    "shivajinagar", "mg road", "brigade road", "sadashivanagar", "rr nagar",
    "kengeri", "hosur road", "sarjapur", "kr puram", "cv raman nagar",
    "banaswadi", "kammanahalli", "rt nagar", "peenya", "yeshwanthpur",
    "nagarbhavi", "vijayanagar", "frazer town", "richmond town", "cox town",
    "ulsoor", "hal", "domlur", "ejipura", "varthur", "bellandur",
    "kadugodi", "brookefield", "mahadevapura", "devanahalli",
    "bommanahalli", "begur", "arekere", "banashankari", "kumaraswamy layout",
    "padmanabhanagar", "wilson garden", "lalbagh", "cubbon park",
]


def classify_report(text: str) -> dict:
    """
    Classify a report by counting keyword hits per category.

    Returns: {category: str, matched_keywords: list[str], score: int}
    """
    lowered = text.lower()

    best_category = "other"
    best_score = 0
    best_keywords: List[str] = []

    for category, keywords in CATEGORY_KEYWORDS.items():
        matched = [kw for kw in keywords if kw in lowered]
        score = len(matched)
        if score > best_score:
            best_score = score
            best_category = category
            best_keywords = matched

    return {
        "category": best_category,
        "matched_keywords": best_keywords,
        "score": best_score,
    }


def is_bangalore(text: str) -> bool:
    """Return True if the text mentions any Bangalore-area identifier."""
    lowered = text.lower()
    return any(identifier in lowered for identifier in BANGALORE_IDENTIFIERS)


def get_routing_preview(text: str, departments: list) -> list:
    """
    Given report text and a list of department dicts (with 'name', 'short_name',
    'categories'), return the departments whose categories overlap with the
    classified category.

    Only returns results if the text mentions Bangalore.
    """
    result = classify_report(text)
    category = result["category"]

    if not is_bangalore(text):
        return []

    if category == "other":
        return []

    matched = []
    for dept in departments:
        dept_cats = dept.get("categories") or []
        if category in dept_cats:
            matched.append({
                "name": dept["name"],
                "short_name": dept.get("short_name"),
            })

    return matched
