from langchain_core.tools import tool                                                                                                                                     
import logging
import json

@tool
def ask_multiple_choice_question(question_text: str, options: list[str]) -> str:
    """
    Ask a multiple-choice question to the user and receives their answer.
    Use this when you have a question to the user and you are able to define
    the options for the user to choose from.

    Args:
        question_text (str): The text of the multiple-choice question.
        options (list[str]): A list of possible answer choices.

    Returns:
        str: The user's selected answer (one of the options).
    """
    logging.info("[MCQ] %s %s", question_text, options)
    ret = {
        "type": "question",
        "data": {
            "type": "mcq",
            "question": question_text,
            "answer_options": options
        }
    }
    return json.dumps(ret)

@tool
def ask_numeric_question(question_text: str) -> float:
    """
    Presents a numeric question to the user and receives their answer.

    The LLM can ask for validation of user input based on defined criteria,
    including minimum and maximum allowed values, and units.

    Args:
        question_text (str): The text of the numeric question.

    Returns:
        float: The user's numeric answer.
    """
    ret = {
        "type": "question",
        "data": {
            "type": "numeric",
            "question": question_text
        }
    }
    return json.dumps(ret)

@tool
def ask_free_text_question(question_text: str) -> float:
    """
    Presents a free form text question to the user.

    This question is 

    Args:
        question_text (str): The text of the free-form question.

    Returns:
        str: The user's answer to the question.
    """
    ret = {
        "type": "question",
        "data": {
            "type": "free_form_text",
            "question": question_text
        }
    }
    return json.dumps(ret)

@tool
def retrieve_obc_section(section: str) -> str:
    """
    Retrieves a section from the Ontario Building Code based on a section number.

    Args:
        section (str): Section number in the format of part.section.sub-section.article

    Returns:
        str: The content of the OBC section.
    """
    logging.info("Asked to retreive section %s", section)
    try:
        return sections[section]
    except:
        return "I could not find the section you requested"

@tool
def provide_final_answer(answer: str) -> str:
    """
    Let user know this is the final answer to form question and there will be no more
    questions regarding this specific form question.

    Args:
        answer (str): The final answer to be used by user to fill the form question
    """
    logging.info("[Final] Answer: %s", answer)
    ret = {
        "type": "form_answer",
        "data": {
            "answer": answer
        }
    }
    return json.dumps(ret)


DEFINED_TOOLS = {
    "ask_numeric_question": ask_numeric_question,
    "ask_multiple_choice_question": ask_multiple_choice_question,
    "retrieve_obc_section": retrieve_obc_section,
    "provide_final_answer": provide_final_answer,
}

sections = {
    "section number" : "section text"
}