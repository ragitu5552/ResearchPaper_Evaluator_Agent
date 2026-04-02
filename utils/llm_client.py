import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def call_llm(prompt: str, temperature: float = 0.2) -> str:
    """
    Call Groq (Llama 3.3 70B). Returns response text.
    All agents route through here — swap MODEL to change the LLM.
    """
    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()
