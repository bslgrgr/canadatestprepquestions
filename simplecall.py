import os
import json
from openai import OpenAI
from dotenv import load_dotenv

def split_by_first_occurrence(text, delimiter):
    parts = text.split(delimiter, 1)
    before_delimiter = parts[0]
    after_delimiter = parts[1] if len(parts) > 1 else ''
    return before_delimiter, after_delimiter

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get the current directory
current_dir = os.getcwd()

# Load system content
with open(current_dir + '/system-role.txt', 'r') as system_content_file:
    system_content = system_content_file.read()

# Load the document content
with open(current_dir + '/request-doc.txt', 'r') as request_file:
    document_content = request_file.read()

document_content_short, _ = split_by_first_occurrence(document_content, "Page: 9")
document_content_1st_part, document_content_2nd_part = split_by_first_occurrence(document_content, "Page: 30")

document_content = document_content_1st_part

# Load previously generated questions
questions_file_path = current_dir + '/questions.json'
if os.path.exists(questions_file_path):
    with open(questions_file_path, 'r') as questions_file:
        previous_questions = json.load(questions_file)
else:
    previous_questions = {"questions": []}

def generate_new_question(system_content, document_content, previous_questions):
    request = f"""
    Based on the following document, generate as many new and unique questions as possible that have not been asked before:

    Document:
    {document_content}

    Previously Generated Questions:
    {json.dumps(previous_questions, indent=2)}
    """

    completion = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": request}
        ]
    )

    new_questions = json.loads(completion.choices[0].message.content)
    return new_questions

def save_questions(questions, file_path):
    with open(file_path, 'w') as questions_file:
        json.dump(questions, questions_file, indent=2)

# Main loop to generate and confirm new questions
while True:
    new_questions = generate_new_question(system_content, document_content, previous_questions)

    for question in new_questions['questions']:
        print("\nNew Question Generated:")
        print(json.dumps(question, indent=2))

        user_input = input("Do you want to add this question? (Press Enter for yes, 'n' for no): ").strip().lower()
        if user_input != 'n':
            previous_questions['questions'].append(question)
            save_questions(previous_questions, questions_file_path)
            print("Question added.")
        else:
            print("Question skipped.")

    user_input = input("Do you want to generate more questions? (Press Enter for yes, 'n' for no): ").strip().lower()
    if user_input == 'n':
        break

print("Finished generating questions.")
