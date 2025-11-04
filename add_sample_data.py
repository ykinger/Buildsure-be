import sqlite3
import uuid
import json
from datetime import datetime

db_path = '/home/nima/repositories/ykinger/Buildsure-be/buildsure.db'

def generate_uuid():
    return str(uuid.uuid4())

def add_sample_data():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Organization
    org_id = generate_uuid()
    org_name = "New Buildsure Client"
    org_description = "A new client organization for Buildsure."
    cursor.execute("INSERT INTO organization (id, name, description) VALUES (?, ?, ?)",
                   (org_id, org_name, org_description))

    # 2. User
    user_id = generate_uuid()
    user_name = "Jane Smith"
    user_email = "jane.smith@newclient.com"
    cursor.execute("INSERT INTO user (id, organization_id, name, email) VALUES (?, ?, ?, ?)",
                   (user_id, org_id, user_name, user_email))

    # 3. Project
    project_id = generate_uuid()
    project_name = "New Residential Complex"
    project_description = "A new multi-unit residential complex project."
    project_status = "in_progress"
    cursor.execute("INSERT INTO project (id, organization_id, user_id, name, description, status) VALUES (?, ?, ?, ?, ?, ?)",
                   (project_id, org_id, user_id, project_name, project_description, project_status))

    # 4. Data Matrix (Blueprint) - New entries
    data_matrix_entries = []
    dm3_id = generate_uuid()
    dm3_number = "OBC-9.8.1.1"
    dm3_title = "Sound Transmission Class"
    dm3_guide = "Guide to sound transmission class requirements."
    dm3_question = "Are walls and floors designed for sound transmission class as per OBC 9.8.1.1?"
    data_matrix_entries.append((dm3_id, dm3_number, None, dm3_title, dm3_guide, dm3_question))

    dm4_id = generate_uuid()
    dm4_number = "OBC-9.9.1.1"
    dm4_title = "Ventilation Requirements"
    dm4_guide = "Guide to ventilation requirements for dwelling units."
    dm4_question = "Is mechanical ventilation provided as per OBC 9.9.1.1?"
    data_matrix_entries.append((dm4_id, dm4_number, "Alt-9.9.1.1", dm4_title, dm4_guide, dm4_question))

    for dm_id, number, alt_number, title, guide, question in data_matrix_entries:
        cursor.execute("INSERT INTO data_matrix (id, number, alternate_number, title, guide, question) VALUES (?, ?, ?, ?, ?, ?)",
                       (dm_id, number, alt_number, title, guide, question))

    # 5. Project Data Matrix (Copy from newly inserted Data Matrix for the new project)
    project_data_matrix_ids = []
    for dm_id, _, _, _, _, _ in data_matrix_entries:
        pdm_id = generate_uuid()
        pdm_status = "Pending"
        pdm_output = json.dumps({"initial_check": "false", "notes": "New project entry"}) # Sample JSON output
        cursor.execute("INSERT INTO project_data_matrix (id, project_id, data_matrix_id, status, output) VALUES (?, ?, ?, ?, ?)",
                       (pdm_id, project_id, dm_id, pdm_status, pdm_output))
        project_data_matrix_ids.append((pdm_id, dm_id)) # Store pdm_id and corresponding dm_id

    # 6. Data Matrix Knowledge Base (Linking new data_matrix entries to *existing* knowledge_base entries)
    # Attempt to find existing knowledge base entries to link to
    # For dm3_id (Sound Transmission Class), try to find a KB entry related to 'Sound' or 'OBC Part 9, Section 8'
    cursor.execute("SELECT id FROM knowledge_base WHERE reference LIKE ? OR content LIKE ? LIMIT 1", ('%OBC Part 9, Section 8%', '%sound%'))
    kb_id_for_dm3 = cursor.fetchone()
    if kb_id_for_dm3:
        dmkb3_id = generate_uuid()
        cursor.execute("INSERT INTO data_matrix_knowledge_base (id, data_matrix_id, knowledge_base_id) VALUES (?, ?, ?)",
                       (dmkb3_id, dm3_id, kb_id_for_dm3[0]))

    # For dm4_id (Ventilation Requirements), try to find a KB entry related to 'Ventilation' or 'OBC Part 9, Section 9'
    cursor.execute("SELECT id FROM knowledge_base WHERE reference LIKE ? OR content LIKE ? LIMIT 1", ('%OBC Part 9, Section 9%', '%ventilation%'))
    kb_id_for_dm4 = cursor.fetchone()
    if kb_id_for_dm4:
        dmkb4_id = generate_uuid()
        cursor.execute("INSERT INTO data_matrix_knowledge_base (id, data_matrix_id, knowledge_base_id) VALUES (?, ?, ?)",
                       (dmkb4_id, dm4_id, kb_id_for_dm4[0]))

    # 7. Message - New entries
    # Find the project_data_matrix_id for dm3_id (Sound Transmission Class) from the newly created PDM entries
    pdm_id_for_message = None
    for pdm_id, dm_id in project_data_matrix_ids:
        if dm_id == dm3_id:
            pdm_id_for_message = pdm_id
            break

    if pdm_id_for_message:
        msg3_id = generate_uuid()
        msg3_role = "user"
        msg3_content = "What are the sound transmission requirements for walls in this new project?"
        cursor.execute("INSERT INTO message (id, project_data_matrix_id, user_id, role, content) VALUES (?, ?, ?, ?, ?)",
                       (msg3_id, pdm_id_for_message, user_id, msg3_role, msg3_content))

        msg4_id = generate_uuid()
        msg4_role = "assistant"
        msg4_content = "OBC 9.8.1.1 specifies that walls separating dwelling units must have a minimum sound transmission class rating of 50."
        cursor.execute("INSERT INTO message (id, project_data_matrix_id, role, content) VALUES (?, ?, ?, ?)",
                       (msg4_id, pdm_id_for_message, msg4_role, msg4_content))


    conn.commit()
    conn.close()
    print("Database populated with new sample data.")

if __name__ == "__main__":
    add_sample_data()