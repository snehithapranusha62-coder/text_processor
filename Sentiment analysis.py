import re
import sqlite3
from datetime import datetime
from multiprocessing import Pool, cpu_count

# SQLite Database File
DB_FILE = "review_analysis.db"

# Sentiment Scoring Dictionary
SCORES = {
    "good": 1, "great": 2, "excellent": 3, "happy": 1,
    "satisfied": 2, "amazing": 2, "fantastic": 3,
    "love": 2, "best": 3,
    "bad": -1, "poor": -2, "sad": -1,
    "terrible": -3, "worst": -3,
    "refund": -2, "return": -1,
    "damaged": -2, "broken": -2,
    "disappointed": -2, "unhappy": -2,
    "useless": -3
}

NEGATIONS = {"not", "never", "no", "hardly"}

REFUND_PATTERNS = [
    r"\brefund\b",
    r"\breplaced\b",
    r"\breturn\b",
    r"\bmoney back\b",
    r"\breplacement\b"
]

REFUND_REGEX = [re.compile(pattern) for pattern in REFUND_PATTERNS]

#Text Cleaning 

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    return text

# Sentiment Analysis

def analyze_review(review):
    try:
        cleaned = clean_text(review)
        words = cleaned.split()

        score = 0
        i = 0

        while i < len(words):
            word = words[i]

            if word in NEGATIONS and i + 1 < len(words):
                next_word = words[i + 1]
                if next_word in SCORES:
                    score -= SCORES[next_word]
                    i += 2
                    continue

            if word in SCORES:
                score += SCORES[word]

            i += 1

        refund_flag = any(regex.search(cleaned) for regex in REFUND_REGEX)

        if score > 0:
            sentiment = "Positive"
        elif score < 0:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        return (review, sentiment, refund_flag)

    except Exception:
        return None

#  Create Database & Table 

def create_database():
    try:
        connection = sqlite3.connect(DB_FILE)
        cursor = connection.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review TEXT,
            sentiment TEXT,
            refund_flag INTEGER,
            created_at TEXT
        )
        """)

        connection.commit()
        cursor.close()
        connection.close()

    except sqlite3.Error as e:
        print("Database Error:", e)

#  Insert Reviews 

def insert_reviews(results):
    try:
        connection = sqlite3.connect(DB_FILE)
        cursor = connection.cursor()

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data_to_insert = [
            (review, sentiment, int(refund_flag), current_time)
            for review, sentiment, refund_flag in results
        ]

        query = """
        INSERT INTO reviews (review, sentiment, refund_flag, created_at)
        VALUES (?, ?, ?, ?)
        """

        cursor.executemany(query, data_to_insert)
        connection.commit()

        cursor.close()
        connection.close()

    except sqlite3.Error as e:
        print("Insert Error:", e)

#  Process Reviews 

def process_reviews(review_list):
    with Pool(cpu_count()) as pool:
        results = pool.map(analyze_review, review_list)

    valid_results = [r for r in results if r is not None]
    corrupted_count = len(results) - len(valid_results)

    if valid_results:
        insert_reviews(valid_results)

    print("Processing Completed Successfully!")
    print(f"Skipped {corrupted_count} corrupted records")

#  Main 

if __name__ == "__main__":
    create_database()

    reviews = [
        "The product is excellent and I am very happy",
        "Amazing quality and great customer service",
        "Super satisfied with the purchase",
        "Fantastic experience and very good support",
        "Loved it, works perfectly",
        "Great value for money",
        "Very happy with fast delivery",
        "Excellent packaging and quality",
        "Highly recommend this product",
        "Best purchase I have made this year",

        "Worst quality, I want refund immediately",
        "Very bad experience and terrible service",
        "Not good at all",
        "The item was damaged and broken",
        "Extremely poor build quality",
        "I need money back for this poor product",
        "Product stopped working after one day",
        "Very disappointed and unhappy",
        "Completely useless and worst purchase",
        "Return this item immediately"
    ]

    process_reviews(reviews)