import os

from openai import OpenAI
from dotenv import load_dotenv

# Get the current directory
current_dir = os.getcwd()

# Read the contents of the first file
with open(current_dir + '/system-role.txt', 'r') as system_content_file:
    system_content = system_content_file.read()

# Read the contents of the second file
with open(current_dir +  '/request-doc.txt', 'r') as request_file:
    request = request_file.read()

# Load environment variables from .env file
load_dotenv()

client = OpenAI()

completion = client.chat.completions.create(
  model="gpt-4o",
  response_format={"type": "json_object"},
  messages=[
    {"role": "system", "content": system_content},
    {"role": "user", "content": request}
  ]
)

print(completion.choices[0].message.content)
# print(completion.choices[0].message)
# print(completion.choices[0])
print(completion)

# Write the dictionary to a JSON file
with open(current_dir + '/questions.json', 'w') as questions_file:
  questions_file.write(completion.choices[0].message.content)