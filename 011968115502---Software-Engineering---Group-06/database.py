import sqlite3

DB_NAME = "phonebook.db"


def connect_db():
    return sqlite3.connect(DB_NAME)


def init_database():
    conn = connect_db()
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        address TEXT,
        group_id INTEGER,
        FOREIGN KEY (group_id) REFERENCES groups(id)
    )
    """)

    conn.commit()
    conn.close()



def insert_contact(name, phone, email=None, address=None, group_id=None):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO contacts (name, phone, email, address, group_id)
    VALUES (?, ?, ?, ?, ?)
    """, (name, phone, email, address, group_id))

    conn.commit()
    conn.close()


def get_all_contacts():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT contacts.id, contacts.name, contacts.phone,
           contacts.email, contacts.address, groups.name
    FROM contacts
    LEFT JOIN groups ON contacts.group_id = groups.id
    ORDER BY contacts.name ASC
    """)

    data = cursor.fetchall()
    conn.close()
    return data


def update_contact(contact_id, name, phone, email, address, group_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE contacts
    SET name=?, phone=?, email=?, address=?, group_id=?
    WHERE id=?
    """, (name, phone, email, address, group_id, contact_id))

    conn.commit()
    conn.close()


def delete_contact(contact_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM contacts WHERE id=?", (contact_id,))

    conn.commit()
    conn.close()


def search_contacts(keyword):
    conn = connect_db()
    cursor = conn.cursor()

    query = f"%{keyword}%"

    cursor.execute("""
    SELECT contacts.id, contacts.name, contacts.phone,
           contacts.email, contacts.address, groups.name
    FROM contacts
    LEFT JOIN groups ON contacts.group_id = groups.id
    WHERE contacts.name LIKE ? OR contacts.phone LIKE ?
    """, (query, query))

    data = cursor.fetchall()
    conn.close()
    return data


def get_all_groups():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM groups")
    data = cursor.fetchall()

    conn.close()
    return data
