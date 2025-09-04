in the project table we have a column curr_task in projects table. for now the value in curr_task will always be code_matrix

we convert the table convo to code_matrix_status

in the code_matrix_status table we will have a column called curr_section, 
curr_section column helps us write the prompt for this particular section


we change the endpoint /api/v1/organizations/<org_id>/projects/start to /api/v1/organizations/<org_id>/project/<project_id>/code-matrix/query
when this endpoint is called we see the current task of project which will be code_matrix(in future UI will be aware of current task so this look up will be redundant actually even now its redundant since it will be code_matrix).
we go to table code_matrix_status get the section we are working on and also get the conversation we need for LLM

the structure of response for this query endpoint will look like this

{
  "id": "unique-session-id-12345",
  "type": "question" | "decision",
  "question": {
    "text": "What type of building are you constructing?",
    "type": "multiple_choice_single" | "multiple_choice_multiple" | "numerical" | "text",
    "options": [
      {"id": "1", "text": "Residential"},
      {"id": "2", "text": "Commercial"},
      {"id": "3", "text": "Industrial"}
    ],
    "validation": {
      "min": 0,
      "max": 100,
      "pattern": "^[A-Za-z0-9 ]+$"
    }
  },
  "decision": {
    "text": "Based on your inputs, we recommend using steel framing for this project.",
    "confidence": 0.85,
    "follow_up_required": true
  },
}




code_matrix_status

