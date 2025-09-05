class PromptBuilder:
    """
    A class for building prompts from a template, conversation history, and current task details.
    """

import glob
import os

class PromptBuilder:
    """
    A class for building prompts from a template, conversation history, and current task details.
    """

    def __init__(self, template_dir: str):
        """
        Initializes the PromptBuilder with the directory containing the prompt template files.

        Args:
            template_dir: The directory containing the prompt template files.
        """
        self.template_dir = template_dir

    def render(
        self,
        current_question_number: str,
        form_questions_and_answers: list[dict],
        clarifying_questions_and_answers: list[dict],
    ) -> str:
        """
        Renders the prompt template with the provided data.

        Args:
            current_question_number: The number of the current form question.
            form_questions_and_answers: A list of dictionaries, where each dictionary
                represents a previously answered form question and its answer.
                Example:
                [
                    {"question_number": 1, "question_title": "Question 1", "answer": "Answer 1"},
                    {"question_number": 2, "question_title": "Question 2", "answer": "Answer 2"},
                ]
            clarifying_questions_and_answers: A list of dictionaries, where each dictionary
                represents a clarifying question and its answer.
                Example:
                [
                    {"question": "Clarifying question 1", "answer": "Answer 1"},
                    {"question": "Clarifying question 2", "answer": "Answer 2"},
                ]

        Returns:
            The rendered prompt as a string.
        """
        prompt = ""
        template = ""
        template_files = sorted(glob.glob(os.path.join(self.template_dir, "*.md")))

        for file_path in template_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read() # .decode('utf-8', errors='replace')
                if "dynamic" in file_path:
                    template = content
                else:
                    prompt += content
            except Exception as e:
                print(f"Error reading file {file_path}: {str(e)}")

        form_questions_and_answers_str = "\n".join(
            [
                f"{i+1}. Question: {q_and_a['question_title']}\n   Answer: {q_and_a['answer']}"
                for i, q_and_a in enumerate(form_questions_and_answers)
            ]
        ) if form_questions_and_answers else "No finalized form questions and answers yet."

        clarifying_questions_and_answers_str = "\n".join(
            [
                f"{i+1}. Question: {q_and_a['question']}\n   Answer: {q_and_a['answer']}"
                for i, q_and_a in enumerate(clarifying_questions_and_answers)
            ]
        ) if len(clarifying_questions_and_answers)>0 else "No clarifying questions asked so far."

        latest_user_answer = clarifying_questions_and_answers[-1]["answer"] if clarifying_questions_and_answers else "No clarifying questions asked so far."
        rendered_template = template.format(
            current_question_number=str(current_question_number),
            form_questions_and_answers_str=form_questions_and_answers_str,
            clarifying_questions_and_answers_str=clarifying_questions_and_answers_str,
            latest_user_answer=f"{latest_user_answer}",
        )

        return prompt + rendered_template
