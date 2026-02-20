import mysql.connector
from mysql.connector import Error
import os
import json
import re
from datetime import datetime
from multiprocessing import Pool, cpu_count
import matplotlib.pyplot as plt


# Rule-Based Sentiment Keywords
POS_KEYWORDS = ["good", "great", "excellent", "happy", "love", "best", "awesome", "perfect", "amazing"]
NEG_KEYWORDS = ["bad", "poor", "terrible", "worst", "hate", "disappointing", "awful", "broken"]

# MySQL Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",       
    "password": "root", 
    "database": "amazondb",
    "ssl_disabled": True   
}

# Text Cleaning
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text

# Calculate Score
def calculate_score(text):
    score = 0
    words = clean_text(text).split()
    for word in words:
        if word in POS_KEYWORDS:
            score += 1
        elif word in NEG_KEYWORDS:
            score -= 1
    return score


# Get Sentiment from Score

def get_sentiment(score):
    if score > 0:
        return "Positive"
    elif score < 0:
        return "Negative"
    else:
        return "Neutral"


# Convert Rating to Sentiment (Ground Truth)
def rating_to_sentiment(rating):
    if rating >= 4:
        return "Positive"
    elif rating <= 2:
        return "Negative"
    else:
        return "Neutral"
# Process Single Review (Multiprocessing)

def process_review(data):
    text = data.get("reviewText", "")
    rating = data.get("overall", 3)

    if not text.strip():
        return None

    score = calculate_score(text)
    predicted = get_sentiment(score)
    actual = rating_to_sentiment(rating)
    timestamp = datetime.now()

    return (text, score, predicted, actual, timestamp)

# Create MySQL Connection
def create_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"MySQL Connection Error: {e}")
        return None

# Create Database & Table

def create_database_and_table():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            ssl_disabled=True
        )
        cursor = conn.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS amazondb")
        cursor.execute("USE amazondb")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                review TEXT,
                score INT,
                predicted_sentiment VARCHAR(20),
                actual_sentiment VARCHAR(20),
                timestamp DATETIME
            )
        """)

        conn.commit()
        conn.close()
        print("Database and table ready.")
    except Error as e:
        print(f"Error creating database: {e}")

# Process File & Store in MySQL (Batch Insert)
def process_file(json_file):
    if not os.path.exists(json_file):
        print("File not found!")
        return

    print("Reading JSON file...")

    data_list = []
    with open(json_file, "r", encoding="utf-8") as file:
        for line in file:
            try:
                data_list.append(json.loads(line))
            except:
                continue

    print(f"Total Reviews Loaded: {len(data_list)}")
    print(f"Using {cpu_count()} CPU cores...\n")

    with Pool(cpu_count()) as pool:
        results = pool.map(process_review, data_list)

    results = [r for r in results if r is not None]

    conn = create_connection()
    if conn is None:
        return

    cursor = conn.cursor()

    batch_size = 1000
    total_inserted = 0

    try:
        for i in range(0, len(results), batch_size):
            batch = results[i:i + batch_size]

            cursor.executemany("""
                INSERT INTO sentiment_results
                (review, score, predicted_sentiment, actual_sentiment, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, batch)

            conn.commit()
            total_inserted += len(batch)
            print(f"Inserted {total_inserted} records...")

        print(f"\nSuccessfully processed {len(results)} reviews!")

    except Error as e:
        print(f"MySQL Insert Error: {e}")

    finally:
        conn.close()

# Calculate Accuracy
def calculate_accuracy():
    conn = create_connection()
    if conn is None:
        return

    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM sentiment_results
        WHERE predicted_sentiment = actual_sentiment
    """)
    correct = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sentiment_results")
    total = cursor.fetchone()[0]

    accuracy = (correct / total) * 100 if total > 0 else 0

    print(f"\nModel Accuracy: {accuracy:.2f}%")
    conn.close()

# Visualization
def visualize_results():
    conn = create_connection()
    if conn is None:
        return

    cursor = conn.cursor()

    cursor.execute("""
        SELECT predicted_sentiment, COUNT(*)
        FROM sentiment_results
        GROUP BY predicted_sentiment
    """)
    data = cursor.fetchall()

    conn.close()

    sentiments = [row[0] for row in data]
    counts = [row[1] for row in data]

    plt.figure()
    plt.bar(sentiments, counts, color=['green', 'blue', 'red'])
    plt.title("Sentiment Distribution")
    plt.xlabel("Sentiment")
    plt.ylabel("Count")
    plt.savefig("sentiment_chart.png")
    plt.show()

    print("Chart saved as sentiment_chart.png")

# Main
if __name__ == "__main__":
    print("Starting MySQL-Based Sentiment Analysis...\n")

    create_database_and_table()
    process_file("Cell_Phones_and_Accessories_5.json")
    calculate_accuracy()
    visualize_results()

    print("\nProject Completed Successfully 🚀")