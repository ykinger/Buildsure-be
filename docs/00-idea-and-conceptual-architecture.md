# 📘 Adaptive AI Wizard for Form Completion — Conceptual Documentation

## Problem Definition
We need an application that:  
- Guides users through a **sequential form** (the “form questions”).  
- Uses an **AI agent** to adaptively break these form questions into simpler **clarifying questions**.  
- Maintains correctness by ensuring final answers always map to **predefined form questions**.  
- Provides contextual explanations by referencing external knowledge bases (Ontario Building Code).  
- Produces a **structured output** (answers to all form questions) that can later be rendered into a final PDF form.  

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
