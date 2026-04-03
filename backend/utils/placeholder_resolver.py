"""
Placeholder Resolver — Detects {variable} placeholders in prompt messages
and substitutes them with realistic sample data so that golden capture
and target execution can produce meaningful outputs for the Judge to compare.
"""
import re
from typing import List, Dict, Any

# Realistic sample data for common variable names
SAMPLE_DATA = {
    "text": (
        "Artificial intelligence has transformed industries worldwide. "
        "From healthcare diagnostics to autonomous vehicles, AI systems "
        "are making decisions that previously required human expertise. "
        "However, concerns about bias, transparency, and job displacement "
        "remain significant challenges that society must address."
    ),
    "review": "This product exceeded my expectations! The quality is outstanding and delivery was super fast. Highly recommend to everyone.",
    "user_request": "What is the price of AAPL right now?",
    "input": "The weather today is sunny with a high of 75 degrees Fahrenheit.",
    "content": "Machine learning models require large datasets for training. Transfer learning can reduce data needs significantly.",
    "query": "What are the main benefits of renewable energy sources?",
    "question": "How does photosynthesis convert sunlight into chemical energy?",
    "message": "Hello, I'd like to schedule a meeting for next Tuesday at 3 PM to discuss the Q3 results.",
    "prompt": "Explain the concept of recursion in programming with a simple example.",
    "document": "The company reported Q3 revenue of $4.2 billion, up 15% year-over-year, driven by strong cloud services growth.",
    "data": '{"name": "John Doe", "age": 30, "city": "New York", "occupation": "Engineer"}',
    "article": "Scientists have discovered a new species of deep-sea fish near hydrothermal vents in the Pacific Ocean. The species exhibits bioluminescence.",
    "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "email": "Subject: Project Update\n\nHi team, the deadline has been moved to Friday. Please submit your deliverables by EOD Thursday.",
    "sentence": "The quick brown fox jumps over the lazy dog.",
    "paragraph": "Climate change poses unprecedented challenges to global ecosystems. Rising temperatures are causing glaciers to melt, sea levels to rise, and weather patterns to become increasingly unpredictable.",
}

# Fallback for any unrecognized variable name
DEFAULT_SAMPLE = "This is a sample input text for testing and evaluation purposes. It contains enough content to produce a meaningful AI response."


def detect_placeholders(text: str) -> List[str]:
    """Find all {variable_name} or {variable name} placeholders in a string."""
    if not text:
        return []
    # Match letters, numbers, underscores, AND spaces inside braces
    return re.findall(r'\{([A-Za-z0-9_\s]+)\}', text)


def substitute_placeholders(text: str) -> str:
    """Replace {variable} placeholders with realistic sample data."""
    if not text:
        return text

    placeholders = detect_placeholders(text)
    if not placeholders:
        return text

    result = text
    for var_name in placeholders:
        # Normalize: 'user request' -> 'user_request'
        normalized_key = var_name.lower().strip().replace(" ", "_")
        sample = SAMPLE_DATA.get(normalized_key, DEFAULT_SAMPLE)
        result = result.replace(f'{{{var_name}}}', sample)

    return result


def substitute_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create a copy of messages with all placeholders substituted.
    Used for golden capture and target execution (not for prompt translation).
    """
    substituted = []
    for msg in messages:
        new_msg = dict(msg)
        if 'content' in new_msg and isinstance(new_msg['content'], str):
            new_msg['content'] = substitute_placeholders(new_msg['content'])
        substituted.append(new_msg)
    return substituted
