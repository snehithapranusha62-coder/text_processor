# DATABASE PERFORMANCE TEST 
import sqlite3
import time
import random
from datetime import datetime

DB_FILE = "performance.db"

# STEP 1: Initialize Database
def setup_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS feedback_data")

    cursor.execute("""
    CREATE TABLE feedback_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feedback_text TEXT,
        rating_score INTEGER,
        rating_type TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()
    print("Step 1 Completed: Database Initialized")


# STEP 2: Sentiment Word Dictionaries (UPDATED)

POSITIVE_WORDS = {"fantastic":3, "awesome":2, "brilliant":3, "wonderful":2, "delight":1}
NEGATIVE_WORDS = {"horrible":-3, "disappointing":-2, "bad":-1, "terrible":-3, "awful":-2}

def generate_feedback():
    words = list(POSITIVE_WORDS.keys()) + list(NEGATIVE_WORDS.keys()) #Combines all positive and negative words into one list.
    sentence = " ".join(random.choices(words, k=10))

    score = 0
    for w in sentence.split():
        score += POSITIVE_WORDS.get(w, 0)
        score += NEGATIVE_WORDS.get(w, 0)

    if score > 0:
        label = "Positive"
    elif score < 0:
        label = "Negative"
    else:
        label = "Neutral"

    return (sentence, score, label, datetime.now().isoformat())

# STEP 3: Insert 1 Million Records (Batch Insert)

def insert_records():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    total_records = 1_000_000
    batch_size = 10_000

    start_time = time.time()

    for i in range(0, total_records, batch_size):
        batch = [generate_feedback() for _ in range(batch_size)]
        cursor.executemany("""
            INSERT INTO feedback_data
            (feedback_text, rating_score, rating_type, created_at)
            VALUES (?, ?, ?, ?)
        """, batch)
        conn.commit()

    end_time = time.time()

    cursor.execute("SELECT COUNT(*) FROM feedback_data")
    total_rows = cursor.fetchone()[0]

    print(f"Total Rows Inserted: {total_rows}")
    print(f"Insertion Time: {round(end_time - start_time, 2)} seconds")

    conn.close()

# STEP 4: Benchmark Queries

def run_queries():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    queries = [
        "SELECT COUNT(*) FROM feedback_data WHERE rating_type='Positive'",
        "SELECT AVG(rating_score) FROM feedback_data",
        "SELECT * FROM feedback_data WHERE rating_score = 3"
    ]

    start = time.time()
    for q in queries:
        cursor.execute(q)
        cursor.fetchall()
    end = time.time()

    conn.close()
    return round(end - start, 2)

# STEP 5: Apply Index Optimization
def apply_indexes():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("CREATE INDEX idx_type ON feedback_data(rating_type)")
    cursor.execute("CREATE INDEX idx_score ON feedback_data(rating_score)")

    conn.commit()
    conn.close()
    print("Indexing Applied Successfully")

# MAIN EXECUTION

if __name__ == "__main__":

    setup_database()
    insert_records()

    before_time = run_queries()
    print(f"Query Time (Before Optimization): {before_time} seconds")

    apply_indexes()

    after_time = run_queries()
    print(f"Query Time (After Optimization): {after_time} seconds")

    improvement = ((before_time - after_time) / before_time) * 100

    print("\nFinal Performance Report")
    print(f"Before Optimization: {before_time} seconds")
    print(f"After Optimization: {after_time} seconds")
    print(f"Performance Improvement: {round(improvement, 2)} %")