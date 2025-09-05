in the project table we have a column curr_task in projects table. for now the value in curr_task will always be code_matrix

we convert the table convo to code_matrix_status

in the code_matrix_status table we will have a column called curr_section, 
curr_section column helps us write the prompt for this particular section


we change the endpoint /api/v1/organizations/<org_id>/projects/start to /api/v1/organizations/<org_id>/project/<project_id>/code-matrix/query
when this endpoint is called we see the current task of project which will be code_matrix(in future UI will be aware of current task so this look up will be redundant actually even now its redundant since it will be code_matrix).
we go to table code_matrix_status get the section we are working on and also get the conversation we need for LLM

the structure of response for this query endpoint will look like this


# TBD
1. UI loads
2. UI calls `/api/v1/organizations/<org_id>/project/<project_id>/code-matrix/query`
3. The controller for that endpoint does what it needs to retrieve:
  a. Project state -> which section are we working on right now?
  b. List of form questions answered so far [AI has answered these]
  c. List of clarifying questions asked and answered so far [AI asked these, user answered]
4. Controller calls AI service to get next "thing"
  a. Next thing could be a clarifying question -> used to work on current form section
  b. Next thing could be an answer decided by AI, that needs to go to UI for "user verification"  




```json
{
  "type": "question",
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
  }
}
```

```json
{
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
    "confidence": 0.85
  }
}
```



code_matrix_status

