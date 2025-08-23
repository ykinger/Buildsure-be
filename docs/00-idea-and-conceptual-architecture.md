# 📘 Adaptive AI Wizard for Form Completion — Conceptual Documentation

## Problem Definition
The intended users of this application are **architects and design professionals** who must ensure that their construction projects comply with the **Ontario Building Code (OBC)**.  

As part of the compliance process, architects are required to complete a standardized **form** that classifies the building’s major occupancy and other characteristics. This form is based on definitions, rules, and criteria set out in the OBC.  

The **problems with the current process** are:  
- Filling out the form is **time-consuming**.  
- Ensuring **accuracy** is difficult because the OBC is large and complex (Volumes 1 and 2 are ~15MB each, spanning thousands of pages).  
- Architects often need to **reference multiple sections and definitions** across the OBC to justify their answers.  

The **opportunity for AI** is clear:  
- The form and the OBC are both **textual and reference-driven**, making them amenable to AI assistance.  
- An AI agent can **ask clarifying questions** in simple language, while ensuring that final answers always map to the official **form questions**.  
- The AI can reference the OBC to provide **definitions and justifications**, increasing trust and accuracy.  

The ultimate goal is to:  
1. Make the process of filling the form **faster and less burdensome** for architects.  
2. Improve **accuracy and compliance** by grounding answers in the OBC.  
3. Generate a completed form that can be **reviewed, justified, and submitted** as part of the regulatory process.  


---

## Terminology
- **Form Questions**  
  - The official, predefined questions in the form.  
  - Fixed, sequential, known in advance.  
  - Answers must be validated and stored as part of the final structured form.  

- **Clarifying Questions**  
  - AI-generated helper questions.  
  - Not predefined — emerge dynamically during conversation.  
  - Purpose: to collect enough detail to confidently resolve the current form question.  
  - Never stored as final outputs — only serve as intermediate reasoning steps.  

---

## Knowledge Base
The system relies on two main sources of knowledge:

1. **Predefined Form (Decision Tree)**  
   - The structure of the form is known in advance.  
   - It consists of a sequential list of **form questions** that must all be answered.  
   - Each question has an expected type of answer (multiple choice or numerical).  
   - This ensures determinism and correctness: the AI cannot invent new “form questions,” it can only resolve them.  

2. **Ontario Building Code (Volumes 1 & 2)**  
   - Two large PDF documents (~15MB each).  
   - Serve as the **reference knowledge base** for definitions, rules, and clarifications.  
   - Queried on-demand by the AI to:  
     - Explain technical terms in simpler language.  
     - Provide justifications for why a certain form answer is correct.  
     - Help interpret ambiguous user answers.  
   - These PDFs are **supporting knowledge**, not the driver of the flow: the predefined form defines what must be answered, the Building Code provides context.  

---

## Roles in the System
- **User (UI)**  
  - Sees questions, provides answers (multiple choice or numerical for MVP).  
  - Stateless: UI only renders whatever backend tells it.  

- **Backend API (Python)**  
  - Manages **sessions** (current form question, past answers).  
  - Maintains **decision tree of form questions**.  
  - Packages **context** to send to AI.  
  - Validates AI outputs against form structure.  
  - Advances through form questions or finalizes the form.  

- **AI Agent (Third-party API)**  
  - Interprets answers.  
  - Breaks down form questions into clarifying questions as needed.  
  - Maps answers to valid choices.  
  - References Ontario Building Code for explanations.  
  - Returns either a clarifying question or a resolved form question answer.  

- **Knowledge Base (Ontario Building Code)**  
  - Large, structured but complex PDFs.  
  - Queried selectively by AI for clarifications.  
  - Never dictates form logic, only provides semantic support.  

---

## Context Management
Each AI call is provided a **context package**, built by backend:  
- Finalized **form questions and answers** so far (session history).  
- **Current form question** under resolution.  
- **Latest user answer** (to form or clarifying question).  
- **Relevant knowledge base excerpts** (optional, retrieved if needed).  

---

## Sequence of Actions (Per Form Question)

1. **UI** shows current form question.  
2. **User** answers (choice/number).  
3. **UI → Backend**: sends answer (session-aware).  
4. **Backend** builds context (history + current answer + optional KB references).  
5. **Backend → AI**: sends context with instruction.  
6. **AI → Backend** decides:  
   - **Case 6.1:** Enough info → return answer to current form question → Backend finalizes and advances.  
   - **Case 6.2:** Not enough info → return clarifying question → Backend stores context and UI renders it.  
   - **Case 6.3:** Can finalize current form question **and** proposes clarifying question for the next → Backend finalizes, advances, forwards clarifying Q.  
   - **Case 6.4:** All form questions resolved → Backend marks session complete and generates final form.  

---

## Mermaid Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Frontend (Renderer)
    participant API as Backend API (Python)
    participant AI as Third-party AI API
    participant KB as Ontario Building Code (Knowledge Base)

    U->>UI: Provides answer (choice/number)
    UI->>API: Send answer + session_id
    API->>API: Update session state (form Q/A history, current question)
    API->>KB: (Optional) Retrieve definitions/excerpts
    API->>AI: Send context {history, current form question, latest answer, KB refs}
    AI-->>API: Response (form answer OR clarifying question)
    alt Case 6.1 Enough info
        API->>API: Finalize current form question
        API-->>UI: Deliver next form question
    else Case 6.2 Needs more info
        API-->>UI: Deliver clarifying question
    else Case 6.3 Finalize + advance
        API->>API: Finalize current form question
        API-->>UI: Deliver clarifying question for next form question
    else Case 6.4 All resolved
        API->>API: Generate final form
        API-->>UI: Deliver completed form for review
    end
    UI->>U: Display question/result
