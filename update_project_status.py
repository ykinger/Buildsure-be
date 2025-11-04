
import sqlite3

db_path = '/home/nima/repositories/ykinger/Buildsure-be/buildsure.db'

def update_project_statuses():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Update projects with 'Planning' status to 'in_progress'
    cursor.execute("UPDATE project SET status = 'in_progress' WHERE status = 'Planning';")
    conn.commit()
    conn.close()
    print("Updated project statuses from 'Planning' to 'in_progress'.")

if __name__ == "__main__":
    update_project_statuses()
