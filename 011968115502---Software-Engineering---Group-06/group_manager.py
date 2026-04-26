from database import connect_db


def create_group(group_name):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
        conn.commit()
        print("Group created successfully!")
    except:
        print("Group already exists!")

    conn.close()


def delete_group(group_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE contacts
    SET group_id = NULL
    WHERE group_id = ?
    """, (group_id,))

    cursor.execute("DELETE FROM groups WHERE id=?", (group_id,))

    conn.commit()
    conn.close()
    print("Group deleted successfully!")


def rename_group(group_id, new_name):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        UPDATE groups
        SET name=?
        WHERE id=?
        """, (new_name, group_id))

        conn.commit()
        print("Group renamed successfully!")
    except:
        print("Error renaming group!")

    conn.close()


def assign_contact_to_group(contact_id, group_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE contacts
    SET group_id=?
    WHERE id=?
    """, (group_id, contact_id))

    conn.commit()
    conn.close()

    print("Contact assigned to group!")


def get_contacts_by_group(group_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, name, phone, email, address
    FROM contacts
    WHERE group_id=?
    """, (group_id,))

    data = cursor.fetchall()
    conn.close()

    return data
