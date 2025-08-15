"""
Todo:
This is a prototype for AI name transliteration. See prompt in (./prompt.md)

Your tasks are the following:
- create a separate library in libs/ for the deepseek client
- Add AI transliteration functionality to the rikishi name generator
- The objective is the generate rikishi shikona in batches of 3 with AI transliteration & interpretation

"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from libs.generators.name import RikishiNameGenerator

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

gen = RikishiNameGenerator()

names = [gen.get() for _ in range(3)]
print(names)

with open("prompt.md") as f:
    system_prompt = f.read()

user_prompt = json.dumps([name[0] for name in names], ensure_ascii=False)

print(user_prompt)

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
]

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    response_format={"type": "json_object"},
)

print(json.loads(response.choices[0].message.content))
