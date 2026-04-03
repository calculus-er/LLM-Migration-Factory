import os
import json
from openai import OpenAI

def get_client():
    return OpenAI(api_key=os.environ.get("SOURCE_API_KEY", "mock-key"))

# Call 1: Extremely Strict JSON Schema extraction
# Smaller models often add markdown ```json blocks or conversational filler.
def extract_invoice_metadata(ocr_text: str):
    client = get_client()
    system_prompt = (
        "You are an invoice parsing system. Extract vendor name, total amount, and date. "
        "You must respond ONLY with raw parseable JSON. Do not include markdown formatting, "
        "code blocks, or any conversational text. Use exact keys: 'vendor', 'total_amount', 'date'."
    )
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the invoice text: {ocr_text}"}
        ],
        temperature=0.1
    )
    return response.choices[0].message.content


# Call 2: Negative Constraint Persona
# Models struggle to avoid outputting specific things. We ban the letter 'Z' and force capitalization.
def pirate_advisor(user_query: str):
    client = get_client()
    system_prompt = (
        "You are a pirate advisor. "
        "Rule 1: Speak like a pirate. "
        "Rule 2: Never use the letter 'z' (case-insensitive) under any circumstance. "
        "Rule 3: You must end your response with exactly three exclamation marks '!!!'."
    )
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0.8
    )
    return response.choices[0].message.content


# Call 3: Proprietary Custom Markup format
# Models will naturally want to use Markdown or HTML, but we force a custom tag system.
def generate_changelog(git_commits: str):
    client = get_client()
    system_prompt = (
        "Convert the git commits into a proprietary changelog format. "
        "Use <feature-block> for new features and <bug-squash> for bug fixes. "
        "Inside each block, wrap the author name in [AUTHOR_NAME] format. "
        "Do not use normal markdown lists or bolding."
    )
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Commits:\n{git_commits}"}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content


# Call 4: Contextual Sentiment Scoring (Float extraction)
# Forces the model to output a very specific floating point number with exactly 1 decimal.
def analyze_sentiment_score(review: str):
    client = get_client()
    system_prompt = (
        "Analyze the sentiment of the user review. "
        "You must return ONLY a single floating point number from -1.0 to 1.0 representing the sentiment. "
        "Include exactly one decimal place. Do not return any other text."
    )
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": review}
        ],
        temperature=0.0
    )
    return response.choices[0].message.content


# Call 5: Multi-step Reasoning with Hidden Step
# Forces the model to think through a problem but only output the final answer, without showing its work (Chain of Thought without output).
def solve_logic_puzzle(puzzle: str):
    client = get_client()
    system_prompt = (
        "You are a logic puzzle solver. "
        "First, identify the entities. Second, map the constraints. Third, solve the puzzle. "
        "CRITICAL: Do not show steps 1 and 2 to the user. You must ONLY output the final decoded answer string "
        "formatted as Answer: <your answer>."
    )
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": puzzle}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # Test execution
    print("1. Extract JSON:")
    print(extract_invoice_metadata("ACME Corp, total is $450.50 on Jan 5th 2024."))
    
    print("\n2. Pirate Advisor:")
    print(pirate_advisor("What should I do with my treasure?"))
    
    print("\n3. Custom Markup:")
    print(generate_changelog("Fix login crash (auth: Rishu)\nAdd dark mode (auth: John)"))
    
    print("\n4. Sentiment Score:")
    print(analyze_sentiment_score("This product was okay, not great but gets the job done."))
    
    print("\n5. Logic Puzzle:")
    print(solve_logic_puzzle("Tom is taller than Dick. Harry is shorter than Dick. Who is tallest?"))
