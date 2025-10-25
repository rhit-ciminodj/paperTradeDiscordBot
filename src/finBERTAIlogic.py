from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import headlineNewsScraper as hns

# Load the pre-trained FinBERT model
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

# Labels from the model (the order matters)
labels = ["negative", "neutral", "positive"]

def analyze_sentiment(text):
    # Tokenize and get model outputs
    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    outputs = model(**inputs)

    # Convert logits to probabilities
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    sentiment_idx = torch.argmax(probs).item()

    return {
        "text": text,
        "sentiment": labels[sentiment_idx],
        "confidence": float(probs[0][sentiment_idx].detach())
    }

def analyze_stock_headlines(symbol):
    headlines = hns.get_stock_headlines(symbol)
    results = []
    for headline in headlines:
        sentiment_result = analyze_sentiment(headline)
        results.append(sentiment_result)
    
    if not results:
        return "⚠️ No headlines found for analysis."
    
    # Calculate average sentiment score
    positive_count = sum(1 for r in results if r["sentiment"] == "positive")
    neutral_count = sum(1 for r in results if r["sentiment"] == "neutral")
    negative_count = sum(1 for r in results if r["sentiment"] == "negative")
    
    total = len(results)
    positive_pct = (positive_count / total) * 100
    
    # Format advice based on sentiment distribution
    advice = ""
    if positive_pct >= 70:
        advice = f"✅ **Highly Positive - lil Dom** sentiment ({positive_count}/{total} positive headlines)"
    elif positive_pct >= 50:
        advice = f"📈 **Positive** sentiment ({positive_count}/{total} positive headlines)"
    elif positive_pct >= 30:
        advice = f"➡️ **Neutral** sentiment ({neutral_count}/{total} neutral headlines)"
    else:
        advice = f"📉 **Negative** sentiment ({negative_count}/{total} negative headlines)"
    
    advice += f"\n  Positive: {positive_count} | Neutral: {neutral_count} | Negative: {negative_count}"
    advice += f"\n  *Based on {total} recent headlines*"
    
    return advice
