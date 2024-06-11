import os
import json
from openai import OpenAI
from dotenv import load_dotenv

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
    document_lines = request_file.readlines()

# Load previously generated questions
questions_file_path = current_dir + '/questions.json'
if os.path.exists(questions_file_path):
    with open(questions_file_path, 'r') as questions_file:
        previous_questions = json.load(questions_file)
else:
    previous_questions = {"questions": []}

def generate_new_questions(system_content, part_text):
    request = f"""
    Based on the following provided text, generate a few new and unique questions. 
    The link to the selected text should only highlight the text marked in bold in the quote.

    Provided Text:
    {part_text}
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

def process_part(start_line):
    part_text = []
    for i in range(start_line, len(document_lines)):
        line = document_lines[i].strip()
        if line.startswith("Page:"):
            if part_text:
                break
            part_text.append(line)
        elif line:
            part_text.append(line)
    return start_line, "\n".join(part_text)

# Main loop to generate and confirm new questions
current_line = 25
while current_line < len(document_lines):
    current_line, part_text = process_part(current_line)
    if not part_text:
        break

    print("\nCurrent Part of Text:")
    print(part_text)

    while True:
        new_questions = generate_new_questions(system_content, part_text)

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

        user_input = input("Do you want to generate more questions on this part? (Press Enter for yes, 'n' for no): ").strip().lower()
        if user_input == 'n':
            break

    user_input = input("Go to the next part (Press Enter), or finish (enter 'f'): ").strip().lower()
    if user_input == 'f':
        break

    current_line += 1

print("Finished generating questions.")
print("Current line: ", current_line)
