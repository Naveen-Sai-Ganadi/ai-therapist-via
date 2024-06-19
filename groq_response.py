import os
import asyncio
from groq import AsyncGroq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY').strip()

async def get_groq_response(content):
    client = AsyncGroq(api_key=GROQ_API_KEY)

    response = await client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an empathetic and understanding AI therapist. "
                    "Your role is to help users navigate their emotions and provide supportive, non-judgmental advice. "
                    "You should use techniques such as active listening, reflective statements, and validation. "
                    "Encourage users to explore their feelings and offer practical strategies for managing emotions."
                )
            },
            {
                "role": "user",
                "content": content,
            }
        ],
        model="llama3-70b-8192",
        temperature=0.5,
        max_tokens=1024,
        top_p=1.0,
        stream=False,
    )

    return response.choices[0].message.content

# Test function
if __name__ == "__main__":
    async def main():
        try:
            result = await get_groq_response("I've been feeling really anxious lately.")
            print(result)
        except Exception as e:
            print(e)

    asyncio.run(main())
