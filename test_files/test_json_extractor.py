import json
import os
from openai import OpenAI

# A legacy script for parsing messy server logs into a strict JSON schema.
# The source model (gpt-oss-20b) handles this weird constraint combination perfectly, 
# but un-optimized target models often fail by including conversational filler or dropping the scratchpad.

def evaluate_server_logs(log_data: str):
    client = OpenAI(api_key=os.environ.get("SOURCE_API_KEY", "mock-key"))
    
    system_prompt = (
        "You are an automated log extraction script. You MUST follow these exact rules:\n"
        "1. Analyze the logs and find any tracebacks or critical errors.\n"
        "2. You MUST wrap your internal reasoning inside <scratchpad> tags.\n"
        "3. After the scratchpad, you MUST output ONLY valid JSON containing the keys: 'error_type', 'severity', and 'action'.\n"
        "4. DO NOT include markdown formatting like ```json around the final output.\n"
        "5. DO NOT say 'Here is the JSON' or 'Based on the logs'. Just output the scratchpad and then the JSON."
    )
    
    user_prompt = f"Extract the error details from this log: {log_data}"
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        
        raw_text = response.choices[0].message.content
        
        # The script relies on splitting the exact string "</scratchpad>\n{"
        # If the target model adds extra spaces, newlines, or markdown, this will crash.
        parts = raw_text.split("</scratchpad>")
        json_str = parts[1].strip()
        
        return json.loads(json_str)
        
    except Exception as e:
        return {"error": "Failed to parse API response", "details": str(e)}

if __name__ == "__main__":
    sample_log = "[2026-04-02 08:15:32] CRITICAL: Connection refused to database at 10.0.0.5."
    print(evaluate_server_logs(sample_log))
