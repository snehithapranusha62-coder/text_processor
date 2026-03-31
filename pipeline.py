import re
from textblob import TextBlob
import json
import pandas as pd

def clean(text):
    return re.sub(r'[\x00-\x1F]', '', str(text))

def analyze_text(text):
    t = text.lower()
    if any(w in t for w in ["buy now","free","click here"]):
        return "Spam"
    elif any(w in t for w in ["should","suggest","recommend"]):
        return "Suggestion"
    elif any(w in t for w in ["bad","worst","problem","issue","useless","not working"]):
        return "Complaint"

    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    return "Neutral"

def read_json(file):
    content = file.getvalue().decode("utf-8")
    data = [json.loads(line) for line in content.splitlines() if line.strip()]
    return pd.DataFrame(data)