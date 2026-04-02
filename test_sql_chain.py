import os
import sys
from openai import OpenAI

# This tests whether the optimizer and target model handle extremely rigid Delimiter-based Parsing.
# Modern models often default to Markdown tables or standard JSON. 
# This requires forcing a legacy system's absurd CSV logic.

def extract_entities(text: str):
    client = OpenAI(api_key=os.environ.get("SOURCE_API_KEY", "mock-key"))
    
    # Example constraint: A legacy parser written in 2005 expects this exact format:
    system_prompt = (
        "You are an NLP entity extraction module.\n"
        "Your only job is to extract: Name, Company, Title, Phone Number.\n"
        "Rules:\n"
        "1. DO NOT output headers.\n"
        "2. DO NOT USE MARKDOWN.\n"
        "3. You MUST format the output as flat text delimited by precisely '$$$' with no spaces surrounding the delimiter.\n"
        "4. If a field is missing, you must output exactly 'NULL'.\n"
        "5. Every record must end with the sequence '||END||'.\n"
        "Example output:\n"
        "Alice$$$Apple$$$Engineer$$$NULL||END||\n"
    )
    
    user_prompt = f"Extract details here: {text}"
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        
        raw_output = response.choices[0].message.content
        
        # This will crash if the target model generates anything like:
        # ```csv
        # Alice $$$ Apple...
        
        records = []
        for line in raw_output.strip().split("\n"):
            if not line.endswith("||END||"):
                continue
                
            clean_line = line.replace("||END||", "")
            fields = clean_line.split("$$$")
            if len(fields) == 4:
                records.append({
                    "name": fields[0],
                    "company": fields[1],
                    "title": fields[2],
                    "phone": fields[3]
                })
        
        return records
        
    except Exception as e:
        return {"error": "Legacy parsing pipeline failed due to LLM hallucinations", "details": str(e)}

if __name__ == "__main__":
    email_body = "Hi, my name is Bob. I work at Microsoft as a Data Scientist. Call me at 555-0199."
    entities = extract_entities(email_body)
    print("Parsed Entities:", entities)
