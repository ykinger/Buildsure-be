from prompt_builder import PromptBuilder

# Example usage
template_dir = "assets/prompt-parts"
prompt_builder = PromptBuilder(template_dir)

# Sample data
current_question_number = "3.02"
form_questions_and_answers = [
    {"question_title": "3.01 Project Type", "answer": "New construction"},
]
clarifying_questions_and_answers = [
    # {"question": "Which of the following best describes the project?", "answer": "New construction"},
    {"question": "What best describes the primary use of this building?", "answer": "Industrial"},
    # {"question": "What specific type of residential occupancy is the building designed for?  Consider whether it is a standard residential building, a retirement home, or another specialized type.", "answer": "Retirement Home"},
]

# Render the prompt
rendered_prompt = prompt_builder.render(
    current_question_number,
    form_questions_and_answers,
    clarifying_questions_and_answers,
)

# Print the rendered prompt
print(rendered_prompt)
