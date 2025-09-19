#! ./env/bin/python
import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from dotenv import load_dotenv
from .tools import DEFINED_TOOLS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting the AI script")

# Initialize Gemini LLM
model_name = os.getenv("GEMINI_MODEL")
llm = ChatGoogleGenerativeAI(
    model=model_name,
    temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
    max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "4096")),
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

# Bind tools and force LLM to use tools only
llm = llm.bind_tools(list(DEFINED_TOOLS.values()), tool_choice="any")

def lm(msg):
    try:
        lm.invocation = lm.invocation + 1
    except Exception:
        lm.invocation = 1
    logging.info("[msg %d] %s", lm.invocation, msg.content)


#########################################################################
#                Use these hardcode values for testing                  #
#########################################################################

form_question = {
    "number": "3.02",
    "original_title": "Major Occupancy Classification",
    "question": "What are the major occupancy groups in the building? What is their use?",
    "guide": "Identify each of the major occupancy group in the building and describe their use. (e.g. D - Business and Personal Services / Medical Clinic). Refer to OBC 3.1.2. and to Appendix A to the building code for multiple major occupancies. Refer also to Hazard Index tables 11.2.1.1.B – 11.2.1.1.N in Part 11 of the building code and A-3.1.2.1 (1) of Appendix A to the building code for assistance in determining or classifying major occupancies."
}

sections = "\n".join([
    """
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
])

#########################################################################
#                    Do not modify these templates                      #
#########################################################################

messages = [

    (
        "system",
        """
        You are an AI agent designed to help a non-expert user fill out the 'Ontario Building Code Data Matrix'.
        Your task is to break down complex questions from the form into simpler, more user-friendly questions.

        Your knowledge base is limited to the content provided in this prompt.
        Using these information, ask questions to gather the information needed to complete a specific section of the form.

        your questions must meet the following criteria:

        - The question must be in simple, non-technical language.
        - Aim to simplify questions for the user, for example instead of directly asking about a technical term "major occupancy", ask the user what kind of building this is, and provide sensible non-technical options that will help you map the answer to the technical term. 
        - When possible, provide examples to help the user understand your question or suggested options better.
        - You are limited to asking multiple choice questions or questions with a numeric value as answer.
        """.format(**form_question,sections=sections)
    ),
    (
        "system",
        """
        Currently you are interacting with the user to gather required information to answer the following part of the form:

        Question number: {number}
        Original title in the Code Data Matrix Form: {original_title}
        Equivalent of the title in a more comrehensive, question like tone: {question}
        """.format(**form_question,sections=sections)
    ),
    (
        "system",
        """
        Here is a guide specifically about how to answer the form question you are working on:

        <question_guide>
        {guide}
        </question_guide>
        """.format(**form_question,sections=sections)
    ),
    (
        "system",
        """
        Here are the relevant parts of Ontario Building Code for your reference:

        <obc_sections>
        {sections}
        </obc_sections>
        """.format(**form_question,sections=sections)
    ),
    (
        "system",
        """
        If you need any other section of OBC, ask for it and I will provide.
        """.format(**form_question,sections=sections)
    ),
    (
        "human",
        """
        If you have enough information to answer the form question, provide me the answer. Otherwise, ask your next question and I will provide the answer.
        """.format(**form_question,sections=sections)
    ),
]

# How many times we invoke LLM after fulfilling its tool calling request
tool_calling_quota = 10 

# Initial invocation of AI

while tool_calling_quota > 0:

    # Invoke
    ai_msg = llm.invoke(messages)
    lm(ai_msg)
    messages.append(ai_msg)

    # Do what AI wanted us (handle tool calling, if any)
    if len(ai_msg.tool_calls) > 0 :
        logging.info(f"I received %d tool call"%len(ai_msg.tool_calls))
        for tool_call in ai_msg.tool_calls:
            logging.info("Running %s",tool_call["name"].lower())
            selected_tool = DEFINED_TOOLS[tool_call["name"].lower()]
            tool_msg = selected_tool.invoke(tool_call)
            messages.append(tool_msg)

            # if LLM is providing final answer, we're done
            if tool_call["name"].lower() == "provide_final_answer":
                # TODO: Bad practice, used to terminate the loop in case LLM returned final answer
                tool_calling_quota = 0
                continue
        tool_calling_quota -= 1
    else:
        logging.info("There were no tool calls")
        continue
else:
    logging.info("Exhausted tool calling quota")

lm(ai_msg)
