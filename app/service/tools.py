from langchain_core.tools import tool                                                                                                                                     
import logging
from random import randint

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
    ret = input("Enter your answer: ")
    # ret = options[randint(0, len(options)-1)]
    logging.info("Choosing %s", ret)
    return ret

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
    logging.info("[numeric] Question %s", question_text)
    return 1.0

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
    return "User was informed of final answer"


DEFINED_TOOLS = {
    "ask_numeric_question": ask_numeric_question,
    "ask_multiple_choice_question": ask_multiple_choice_question,
    "retrieve_obc_section": retrieve_obc_section,
    "provide_final_answer": provide_final_answer,
}

sections = {
    "3.1.2" : """
    # 3.1.2. Classification of Buildings or Parts of Buildings by Major Occupancy (See Note A-3.1.2.)

#### 3.1.2.1. Classification of Buildings

**(1)** Except as permitted by Articles 3.1.2.3. to 3.1.2.7., every *building* or part thereof shall be classified according to its *major occupancy* as belonging to one of the Groups or Divisions described in Table 3.1.2.1. (See Note A-3.1.2.1.(1))

**(2)** A *building* intended for use by more than one *major occupancy* shall be classified according to all *major occupancies* for which it is used or intended to be used.

| Group | Division | Description of Major Occupancies                                                       |
|-------|----------|----------------------------------------------------------------------------------------|
| A     | 1        | Assembly occupancies<br>intended for the production and viewing of the performing arts |
| A     | 2        | Assembly occupancies<br>not elsewhere classified in Group A                            |
| A     | 3        | Assembly occupancies<br>of the arena type                                              |
| A     | 4        | Assembly occupancies<br>in which occupants are gathered in the open air                |
| B     | 1        | Detention occupancies                                                                  |
| B     | 2        | Care and treatment occupancies                                                         |
| B     | 3        | Care occupancies                                                                       |
| C     |          | Residential occupancies                                                                |
| D     |          | Business and personal services occupancies                                             |
| E     |          | Mercantile occupancies                                                                 |
| F     | 1        | High-hazard industrial occupancies                                                     |
| F     | 2        | Medium-hazard industrial occupancies                                                   |
| F     | 3        | Low-hazard industrial occupancies                                                      |

#### **Table 3.1.2.1. Major Occupancy Classification** Forming Part of Sentences 3.1.2.1.(1), 3.1.2.2.(1) and 3.11.2.1.(3)

#### 3.1.2.2. Occupancies of the Same Classification

**(1)** Any *building* is deemed to be occupied by a single *major occupancy*, notwithstanding its use for more than one *major occupancy*, provided that all *occupancies* are classified as belonging to the same Group classification or, where the Group is divided into Divisions, as belonging to the same Division classification described in Table 3.1.2.1.

#### 3.1.2.3. Arena-Type Buildings

**(1)** An arena-type *building* intended for occasional use for trade shows and similar exhibition purposes shall be classified as Group A, Division 3 *occupancy*. **e1**

#### 3.1.2.4. Police Stations

**(1)** A police station with detention quarters is permitted to be classified as a Group B, Division 2 *major occupancy* provided the station is not more than 1 *storey* in *building height* and 600 m<sup>2</sup> in *building area*.

### 3.1.2.5. Group B, Division 3 Occupancies

**(1)** Group B, Division 3 *occupancies* are permitted to be classified as Group C *major occupancies* within the application of Part 3 provided

- (a) the occupants live as a single housekeeping unit in a *suite* with sleeping accommodation for not more than 10 persons, and
- (b) not more than two occupants require assistance in evacuation in case of an emergency.

### 3.1.2.6. Storage of Combustible Fibres

**(1)** *Buildings* or parts of thereof used for the storage of baled *combustible fibres* shall be classified as *medium-hazard industrial occupancies*.

### 3.1.2.7. Restaurants

**(1)** A restaurant is permitted to be classified as a Group E *major occupancy* within the application of Part 3 provided the restaurant is designed to accommodate not more than 30 persons consuming food or drink.
    """
}