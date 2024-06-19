import os
import json
import random
from openai import OpenAI
from dotenv import load_dotenv
import jsonschema
from jsonschema import validate

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

# Define the schema for the questions JSON
question_schema = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "possible_answers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "answer_text": {"type": "string"},
                                "is_correct": {"type": "boolean"}
                            },
                            "required": ["answer_text", "is_correct"]
                        }
                    },
                    "quote": {"type": "string"},
                    "page_number": {"type": "number"},
                    "paragraph": {"type": "string"},
                    "online_page": {"type": "string"}
                },
                "required": ["question", "possible_answers", "quote", "page_number", "paragraph", "online_page"]
            }
        }
    },
    "required": ["questions"]
}

# Validate the new questions JSON
def validate_questions_json(questions, questions_name):
    try:
        validate(instance=questions, schema=question_schema)
        print(questions_name + " JSON is valid.")
        return True
    except jsonschema.exceptions.ValidationError as err:
        print(questions_name + " JSON is invalid:", err)
        return False


def get_random_examples(previous_questions, num_examples=3):
    if len(previous_questions['questions']) <= num_examples:
        return previous_questions['questions']
    return random.sample(previous_questions['questions'], num_examples)

def generate_new_questions(system_content, part_text, previous_questions):
    examples = get_random_examples(previous_questions)
    example_text = json.dumps({"questions": examples}, indent=2)

    request = f"""
    Based on the following provided text, generate a few new and unique questions. 
    The link to the selected text should only highlight the text marked in bold in the quote.

    Provided Text:
    {part_text}

    Here are some examples of previously generated questions:
    {example_text}
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
    cur_line = start_line
    for i in range(start_line, len(document_lines)):
        line = document_lines[i].strip()
        if line.startswith("Page:"):
            if part_text:
                break
            part_text.append(line)
        elif line:
            part_text.append(line)
        cur_line = i
    return cur_line, "\n".join(part_text)

# Validate current questions
validate_questions_json(previous_questions, "Existed questions")

# Main loop to generate and confirm new questions
current_line = 274
while current_line < len(document_lines):
    current_line, part_text = process_part(current_line)
    if not part_text:
        break

    print("\nCurrent Part of Text:")
    print(part_text)

    while True:
        new_questions = generate_new_questions(system_content, part_text, previous_questions)

        if validate_questions_json(new_questions, "New questions"):
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
        else:
            print("Generated questions are invalid, skipping.")

        user_input = input("Do you want to generate more questions on this part? (Press Enter for yes, 'n' for no): ").strip().lower()
        if user_input == 'n':
            break

    user_input = input("Go to the next part (Press Enter), or finish (enter 'f'): ").strip().lower()
    if user_input == 'f':
        break

    current_line += 1

print("Finished generating questions.")
print("Current line: ", current_line)
