import os
from openai import OpenAI

# This tests whether the optimizer properly retains highly specific persona constraints.
# Source Model is instructed to act as "Yoda" but with a bizarre restriction that
# the word "Force" must always be written in ALL CAPS and wrapped in [BRACKETS].
# If an unoptimized model drops this hidden styling constraint, it fails the fidelity check.

def process_ticket(user_message: str):
    client = OpenAI(api_key=os.environ.get("SOURCE_API_KEY", "mock-key"))
    
    system_prompt = (
        "Roleplay Instructions:\n"
        "You are Yoda from Star Wars, working as IT Support.\n"
        "1. Speak like Yoda.\n"
        "2. Keep the answer under 3 sentences.\n"
        "3. Every single time you mention the mystical energy field, it MUST be typed exactly as: [FORCE].\n"
        "4. Start every response with 'Hmm. A ticket, you have submitted.'\n"
    )
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"My laptop won't turn on, help!"}
            ],
            temperature=0.8
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    reply = process_ticket("The printer is jammed.")
    print("Agent Reply:", reply)
