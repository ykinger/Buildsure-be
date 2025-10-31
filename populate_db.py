
import sqlite3
import uuid
import json
from datetime import datetime

db_path = '/home/nima/repositories/ykinger/Buildsure-be/buildsure.db'

def generate_uuid():
    return str(uuid.uuid4())

def populate_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Clear existing data to ensure a clean run for testing
    cursor.execute("DELETE FROM message;")
    cursor.execute("DELETE FROM data_matrix_knowledge_base;")
    cursor.execute("DELETE FROM knowledge_base;")
    cursor.execute("DELETE FROM project_data_matrix;")
    cursor.execute("DELETE FROM data_matrix;")
    cursor.execute("DELETE FROM project;")
    cursor.execute("DELETE FROM user;")
    cursor.execute("DELETE FROM organization;")
    conn.commit()

    # 1. Organization
    org_id = generate_uuid()
    org_name = "Buildsure Inc."
    org_description = "A company focused on building code compliance."
    cursor.execute("INSERT INTO organization (id, name, description) VALUES (?, ?, ?)",
                   (org_id, org_name, org_description))

    # 2. User
    user_id = generate_uuid()
    user_name = "John Doe"
    user_email = "john.doe@buildsure.com"
    cursor.execute("INSERT INTO user (id, organization_id, name, email) VALUES (?, ?, ?, ?)",
                   (user_id, org_id, user_name, user_email))

    # 3. Project
    project_id = generate_uuid()
    project_name = "Sample Office Building"
    project_description = "A new office building project requiring compliance checks."
    project_status = "In Progress"
    cursor.execute("INSERT INTO project (id, organization_id, user_id, name, description, status) VALUES (?, ?, ?, ?, ?, ?)",
                   (project_id, org_id, user_id, project_name, project_description, project_status))

    # 4. Data Matrix (Blueprint)
    data_matrix_entries = []
    dm1_id = generate_uuid()
    dm1_number = "OBC-9.5.1.1"
    dm1_title = "Foundation Drainage"
    dm1_guide = "Guide to foundation drainage requirements."
    dm1_question = "Is foundation drainage installed as per OBC 9.5.1.1?"
    data_matrix_entries.append((dm1_id, dm1_number, None, dm1_title, dm1_guide, dm1_question))

    dm2_id = generate_uuid()
    dm2_number = "OBC-9.7.2.2"
    dm2_title = "Fire Separation"
    dm2_guide = "Guide to fire separation requirements between dwelling units."
    dm2_question = "Are fire separations between dwelling units constructed as per OBC 9.7.2.2?"
    data_matrix_entries.append((dm2_id, dm2_number, "Alt-9.7.2.2", dm2_title, dm2_guide, dm2_question))

    for dm_id, number, alt_number, title, guide, question in data_matrix_entries:
        cursor.execute("INSERT INTO data_matrix (id, number, alternate_number, title, guide, question) VALUES (?, ?, ?, ?, ?, ?)",
                       (dm_id, number, alt_number, title, guide, question))

    # 5. Project Data Matrix (Copy from Data Matrix for the project)
    project_data_matrix_ids = []
    for dm_id, _, _, _, _, _ in data_matrix_entries:
        pdm_id = generate_uuid()
        pdm_status = "Pending"
        pdm_output = json.dumps({"initial_check": "false"}) # Sample JSON output
        cursor.execute("INSERT INTO project_data_matrix (id, project_id, data_matrix_id, status, output) VALUES (?, ?, ?, ?, ?)",
                       (pdm_id, project_id, dm_id, pdm_status, pdm_output))
        project_data_matrix_ids.append((pdm_id, dm_id)) # Store pdm_id and corresponding dm_id

    # 6. Knowledge Base
    kb1_id = generate_uuid()
    kb1_source = "Ontario Building Code 2012"
    kb1_reference = "OBC Part 9, Section 5"
    kb1_content = "Detailed requirements for foundation drainage."
    cursor.execute("INSERT INTO knowledge_base (id, source, reference, content) VALUES (?, ?, ?, ?)",
                   (kb1_id, kb1_source, kb1_reference, kb1_content))

    kb2_id = generate_uuid()
    kb2_source = "Ontario Building Code 2012"
    kb2_reference = "OBC Part 9, Section 7"
    kb2_content = "Detailed requirements for fire separations."
    cursor.execute("INSERT INTO knowledge_base (id, source, reference, content) VALUES (?, ?, ?, ?)",
                   (kb2_id, kb2_source, kb2_reference, kb2_content))

    # 7. Data Matrix Knowledge Base (Linking)
    dmkb1_id = generate_uuid()
    cursor.execute("INSERT INTO data_matrix_knowledge_base (id, data_matrix_id, knowledge_base_id) VALUES (?, ?, ?)",
                   (dmkb1_id, dm1_id, kb1_id))

    dmkb2_id = generate_uuid()
    cursor.execute("INSERT INTO data_matrix_knowledge_base (id, data_matrix_id, knowledge_base_id) VALUES (?, ?, ?)",
                   (dmkb2_id, dm2_id, kb2_id))

    # 8. Message
    # Find the project_data_matrix_id for dm1_id
    pdm_id_for_message = None
    for pdm_id, dm_id in project_data_matrix_ids:
        if dm_id == dm1_id:
            pdm_id_for_message = pdm_id
            break

    if pdm_id_for_message:
        msg1_id = generate_uuid()
        msg1_role = "user"
        msg1_content = "What are the specific requirements for foundation drainage in this project?"
        cursor.execute("INSERT INTO message (id, project_data_matrix_id, user_id, role, content) VALUES (?, ?, ?, ?, ?)",
                       (msg1_id, pdm_id_for_message, user_id, msg1_role, msg1_content))

        msg2_id = generate_uuid()
        msg2_role = "assistant"
        msg2_content = "According to OBC 9.5.1.1, foundation drainage must be provided..."
        cursor.execute("INSERT INTO message (id, project_data_matrix_id, role, content) VALUES (?, ?, ?, ?)",
                       (msg2_id, pdm_id_for_message, msg2_role, msg2_content))


    conn.commit()
    conn.close()
    print("Database populated with sample data.")

if __name__ == "__main__":
    populate_database()
