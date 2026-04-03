import os
from openai import OpenAI
from typing import List, Dict

# Initialize the OpenAI client
# This will be picked up by the LLM Migration Factory and refactored
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "dummy_key"))

def summarize_text(text: str) -> str:
    """A generic function to summarize a long text document."""
    print("Summarizing text...")
    
    # First OpenAI call site
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a highly capable summarization assistant. Extract the core points from the provided text and output them as a concise bulleted list."},
            {"role": "user", "content": f"Please summarize the following text:\n\n{text}"}
        ],
        temperature=0.4,
        max_tokens=500
    )
    
    return response.choices[0].message.content

def classify_sentiment(reviews: List[str]) -> List[Dict[str, str]]:
    """A generic function to classify the sentiment of a list of reviews."""
    print(f"Classifying sentiment for {len(reviews)} reviews...")
    
    results = []
    for review in reviews:
        # Second OpenAI call site
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a sentiment analysis engine. Classify the user's review as purely 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'. Output only the single classification word."},
                {"role": "user", "content": review}
            ],
            temperature=0.0,
            max_tokens=10
        )
        
        classification = response.choices[0].message.content.strip()
        results.append({"review": review, "sentiment": classification})
        
    return results

def main():
    print("Starting Dummy App...")
    
    sample_article = "The quick brown fox jumps over the lazy dog. It was a bright cold day in April, and the clocks were striking thirteen."
    summary = summarize_text(sample_article)
    print("Summary:", summary)
    
    sample_reviews = [
        "This product is absolutely amazing! I love it.",
        "Terrible experience. Will never buy again.",
        "It's okay, nothing special but it works."
    ]
    sentiments = classify_sentiment(sample_reviews)
    print("Sentiments:", sentiments)

if __name__ == "__main__":
    main()
