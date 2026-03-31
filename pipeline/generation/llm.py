from google import genai
from ..config import GEMINI_API_KEY
from .prompt import build_prompt


def get_latest_flash_model():
    client = genai.Client(api_key=GEMINI_API_KEY)
    for m in client.models.list():
        if 'gemini' in m.name and 'flash' in m.name:
            return m.name
    return "gemini-2.0-flash"


def generate_answer(question, chunks):
    client = genai.Client(api_key=GEMINI_API_KEY)
    model_name = get_latest_flash_model()
    print(f"Using model: {model_name}")
    prompt = build_prompt(question, chunks)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    return response.text
