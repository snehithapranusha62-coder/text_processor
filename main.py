
# ==========================================
# IMPORT REQUIRED MODULES
# ==========================================

import multiprocessing   #To process the multiprocessing
import time  #To estimate the time of each processing
import csv   #To save the all output in text(CSV)


# ==========================================
# SENTIMENT RULES
# ==========================================

positive_words = ["good", "excellent", "amazing"]
negative_words = ["bad", "worst", "poor"]


# ==========================================
# HEAVY COMPUTATION (Makes CPU Busy)
# ==========================================

def heavy_computation():
    total = 0
    for i in range(500000):   # Increase if needed
        total += i * i
    return total


# ==========================================
# ANALYZE ONE REVIEW
# ==========================================

def analyze_review(review):

    heavy_computation()  # Simulate CPU work

    review = review.lower()

    if any(word in review for word in positive_words):
        return "Positive", 1
    elif any(word in review for word in negative_words):
        return "Negative", -1
    else:
        return "Neutral", 0


# ==========================================
# PROCESS ONE FILE
# ==========================================

def process_file(filename, shared_list):

    positive_count = 0
    negative_count = 0
    neutral_count = 0
    total_score = 0

    print(f"\nProcessing File: {filename} | Process ID: {multiprocessing.current_process().pid}")

    with open(filename, "r") as file:
        for line in file:

            review = line.strip()

            sentiment, score = analyze_review(review)

            total_score += score

            if sentiment == "Positive":
                positive_count += 1
            elif sentiment == "Negative":
                negative_count += 1
            else:
                neutral_count += 1

            # Show processing
            print(f"[{filename}] {review} → {sentiment}")

            shared_list.append([filename, review, sentiment, score])

    print(f"Finished File: {filename}")

    return positive_count, negative_count, neutral_count, total_score


# ==========================================
# MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    files = ["review1.txt", "review2.txt", "review3.txt", "review4.txt"]

    # =====================================================
    # SINGLE PROCESSING
    # =====================================================

    print("\n===== SINGLE PROCESSING STARTED =====")

    start_time = time.time()

    single_results = []
    total_pos = total_neg = total_neu = total_score = 0

    for file in files:
        pos, neg, neu, score = process_file(file, single_results)
        total_pos += pos
        total_neg += neg
        total_neu += neu
        total_score += score

    single_time = time.time() - start_time

    print("\n===== SINGLE PROCESSING COMPLETED =====")
    print(f"Single Processing Time: {single_time:.4f} seconds")


    # =====================================================
    # MULTIPROCESSING
    # =====================================================

    print("\n===== MULTIPROCESSING STARTED =====")

    start_time = time.time()

    manager = multiprocessing.Manager()
    multi_results = manager.list()

    processes = []

    for file in files:
        p = multiprocessing.Process(target=process_file, args=(file, multi_results))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    multi_time = time.time() - start_time

    print("\n===== MULTIPROCESSING COMPLETED =====")
    print(f"Multiprocessing Time: {multi_time:.4f} seconds")


    # =====================================================
    # SAVE RESULTS TO CSV
    # =====================================================

    with open("output.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Filename", "Review", "Sentiment", "Score"])
        writer.writerows(multi_results)

    print("\nResults saved to output.csv")


    # =====================================================
    # PERFORMANCE COMPARISON
    # =====================================================

    print("\n===== PERFORMANCE COMPARISON =====")
    print(f"Single Processing Time: {single_time:.4f} seconds")
    print(f"Multiprocessing Time: {multi_time:.4f} seconds")

    if multi_time < single_time:
        print("Multiprocessing is Faster")
    else:
        print("Single Processing is Faster")


    # =====================================================
    # FINAL SUMMARY
    # =====================================================

    print("\n===== FINAL SUMMARY =====")
    print(f"Total Positive Reviews: {total_pos}")
    print(f"Total Negative Reviews: {total_neg}")
    print(f"Total Neutral Reviews: {total_neu}")
    print(f"Overall Sentiment Score: {total_score}")