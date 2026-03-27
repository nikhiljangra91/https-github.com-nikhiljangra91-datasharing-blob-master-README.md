"""
Auto-categorizer for financial transactions based on merchant/payee keywords.
"""

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Food": [
        "swiggy", "zomato", "domino", "dominos", "mcdonald", "kfc", "pizza hut",
        "subway", "burger king", "dunkin", "starbucks", "cafe coffee day", "ccd",
        "restaurant", "cafe", "bistro", "eatery", "dhaba", "canteen", "bakery",
        "barbeque", "bbnation", "barbeque nation", "haldiram", "bikaner", "wow momo",
        "fassos", "box8", "rebel foods", "freshmenu", "licious", "milkbasket",
        "dunzo", "zepto", "blinkit", "instamart", "grofers", "jiomart",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "meesho", "ajio", "nykaa", "snapdeal",
        "shopsy", "tatacliq", "reliance digital", "croma", "vijay sales",
        "lifestyle", "westside", "pantaloons", "shoppers stop", "max fashion",
        "zara", "h&m", "uniqlo", "decathlon", "ikea", "pepperfry",
        "urban ladder", "firstcry", "hopscotch", "lenskart",
    ],
    "Groceries": [
        "bigbasket", "grofers", "blinkit", "jiomart", "milkbasket", "nature basket",
        "more supermarket", "dmart", "reliance fresh", "star bazaar", "spencers",
        "easyday", "big bazaar", "lulu", "hypermarket", "supermarket",
    ],
    "Utilities": [
        "electricity", "electric", "power bill", "water bill", "gas bill",
        "bses", "tata power", "adani electricity", "mahanagar gas",
        "indraprastha gas", "igl", "mgl", "bescom", "tneb", "msedcl",
        "airtel", "jio", "vodafone", "vi ", "bsnl", "mtnl", "act fibernet",
        "hathway", "den network", "d2h", "tata sky", "dish tv",
        "broadband", "recharge", "postpaid",
    ],
    "Travel": [
        "uber", "ola", "rapido", "meru", "jugnoo", "blablacar",
        "irctc", "indian railway", "rail ticket",
        "indigo", "spicejet", "air india", "vistara", "goair", "akasa",
        "makemytrip", "goibibo", "yatra", "easemytrip", "cleartrip",
        "redbus", "abhibus", "ksrtc", "gsrtc", "dtc",
        "metro", "dmrc", "bmtc", "best bus", "paytm travel",
        "oyo", "treebo", "fabhotel", "zostel", "airbnb", "hotel",
        "petrol", "fuel", "hp petrol", "indian oil", "bharat petroleum", "iocl",
    ],
    "Healthcare": [
        "pharmacy", "chemist", "medical store", "apollo pharmacy", "medplus",
        "1mg", "netmeds", "pharmeasy", "tata 1mg", "healthkart",
        "apollo hospital", "fortis", "max hospital", "aiims", "medanta",
        "hospital", "clinic", "diagnostic", "pathlab", "dr. ", "doctor",
        "insurance health", "star health", "niva bupa", "care health",
    ],
    "Entertainment": [
        "netflix", "hotstar", "disney+", "amazon prime", "jiocinema", "zee5",
        "sony liv", "voot", "mxplayer", "alt balaji",
        "spotify", "gaana", "jiosaavn", "wynk", "hungama",
        "bookmyshow", "pvr", "inox", "carnival cinemas", "cinepolis",
        "gaming", "steam", "playstation", "xbox", "google play",
    ],
    "Finance": [
        "insurance", "lic", "hdfc life", "icici pru", "sbi life", "bajaj allianz",
        "mutual fund", "sip", "zerodha", "groww", "upstox", "kite", "coin",
        "loan", "emi", "credit card bill", "cc bill",
        "nps", "ppf", "fd ", "fixed deposit", "rd ", "recurring deposit",
        "bajaj finance", "hdfc sec", "motilal oswal",
    ],
    "Education": [
        "byju", "unacademy", "vedantu", "toppr", "coursera", "udemy",
        "college fee", "school fee", "tuition", "coaching", "edtech",
        "book", "stationery",
    ],
    "ATM": [
        "atm withdrawal", "atm cash", "cash withdrawal",
    ],
}


def categorize(merchant: str | None, raw_message: str = "") -> str:
    """
    Return a category string for a transaction based on merchant name
    and/or the raw SMS message.
    """
    search_text = " ".join(filter(None, [merchant, raw_message])).lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in search_text:
                return category

    return "Other"
