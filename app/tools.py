def ask_multiple_choice_question(question_text: str, options: list[str]) -> str:
    """
    Presents a multiple-choice question to the user and receives their answer.

    Args:
        question_text (str): The text of the multiple-choice question.
        options (list[str]): A list of possible answer choices.

    Returns:
        str: The user's selected answer (one of the options).
    """
    pass

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
    pass

def retrieve_obc_section(section: str) -> str:
    """
    Retrieves a section from the Ontario Building Code based on a section number.

    Args:
        section (str): Section number in the format of part.section.sub-section.article

    Returns:
        str: The content of the OBC section.
    """
    pass
