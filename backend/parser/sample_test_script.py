import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_system_report(data: str):
    print("Generating report using OpenAI...")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful data analyst."},
            {"role": "user", "content": f"Analyze this data and output a JSON format summary: {data}"}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    result = generate_system_report("Sales are up 20% in Q3.")
    print(result)
