import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

resposta = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Responda só: ok",
)
print(resposta.text)