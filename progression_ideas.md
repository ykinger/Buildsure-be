in the project table we havea column curr_task. for now the value in curr_task will always be code_matrix

we convert the table convo to code_matrix_status

in the code_matrix_status table we have a column called curr_section
curr_section column helps us write the prompt for this particular section


we change the endpoint /api/v1/organizations/<org_id>/projects/start to /api/v1/organizations/<org_id>/projects/query
when this endpoint is called we see the current task of project which will be code_matrix(in future UI will be aware of current task so this look up will be redundant actually even now its redundant since it will be code_matrix).
we go to table code_matrix_status get the section we are working on and also get the conversation we need for LLM