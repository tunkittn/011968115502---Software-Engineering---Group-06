"""SQLite data access layer for the Phone Book Management System."""

import os
import sqlite3

DB_NAME = "phonebook.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)


def connect_db():
    """Create a SQLite connection with rows accessible by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Create database tables and indexes if they do not already exist."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                address TEXT,
                group_id INTEGER,
                FOREIGN KEY (group_id)
                    REFERENCES groups(id)
                    ON UPDATE CASCADE
                    ON DELETE SET NULL
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_contacts_group ON contacts(group_id)"
        )
        conn.commit()
    finally:
        conn.close()


def _contacts_from_rows(rows):
    return [dict(row) for row in rows]


def insert_contact(name, phone, email="", address="", group_id=None):
    """Insert a contact and return the new contact id."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO contacts (name, phone, email, address, group_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, phone, email, address, group_id),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_contacts():
    """Return all contacts sorted alphabetically by name."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                contacts.id,
                contacts.name,
                contacts.phone,
                contacts.email,
                contacts.address,
                contacts.group_id,
                groups.name AS group_name
            FROM contacts
            LEFT JOIN groups ON contacts.group_id = groups.id
            ORDER BY LOWER(contacts.name), contacts.name
            """
        )
        return _contacts_from_rows(cursor.fetchall())
    finally:
        conn.close()


def get_contact_by_id(contact_id):
    """Return one contact by id, or None when it does not exist."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                contacts.id,
                contacts.name,
                contacts.phone,
                contacts.email,
                contacts.address,
                contacts.group_id,
                groups.name AS group_name
            FROM contacts
            LEFT JOIN groups ON contacts.group_id = groups.id
            WHERE contacts.id = ?
            """,
            (contact_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_contact(contact_id, name, phone, email="", address="", group_id=None):
    """Update a contact and return the number of affected rows."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE contacts
            SET name = ?, phone = ?, email = ?, address = ?, group_id = ?
            WHERE id = ?
            """,
            (name, phone, email, address, group_id, contact_id),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def phone_exists(phone, exclude_contact_id=None):
    """Check if a phone number already exists in the database."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        if exclude_contact_id is None:
            cursor.execute("SELECT id FROM contacts WHERE phone = ?", (phone,))
        else:
            cursor.execute(
                "SELECT id FROM contacts WHERE phone = ? AND id != ?",
                (phone, exclude_contact_id),
            )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def delete_contact(contact_id):
    """Delete a contact and return the number of affected rows."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def search_contacts(keyword):
    """Search contacts by name, phone number, or group name."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        pattern = f"%{keyword.strip()}%"
        cursor.execute(
            """
            SELECT
                contacts.id,
                contacts.name,
                contacts.phone,
                contacts.email,
                contacts.address,
                contacts.group_id,
                groups.name AS group_name
            FROM contacts
            LEFT JOIN groups ON contacts.group_id = groups.id
            WHERE contacts.name LIKE ?
               OR contacts.phone LIKE ?
               OR groups.name LIKE ?
            ORDER BY LOWER(contacts.name), contacts.name
            """,
            (pattern, pattern, pattern),
        )
        return _contacts_from_rows(cursor.fetchall())
    finally:
        conn.close()


def create_group(name):
    """Create a group and return the new group id."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO groups (name) VALUES (?)", (name,))
        except sqlite3.IntegrityError as exc:
            raise ValueError("Group name already exists.") from exc
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_groups():
    """Return all groups sorted alphabetically."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM groups ORDER BY LOWER(name), name")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def rename_group(group_id, new_name):
    """Rename a group and return the number of affected rows."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE groups SET name = ? WHERE id = ?",
                (new_name, group_id),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Group name already exists.") from exc
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def delete_group(group_id):
    """Delete a group. Contacts in the group are kept with no group."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE contacts SET group_id = NULL WHERE group_id = ?",
            (group_id,),
        )
        cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def assign_contact_to_group(contact_id, group_id):
    """Assign a contact to a group, or clear the group when group_id is None."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE contacts SET group_id = ? WHERE id = ?",
            (group_id, contact_id),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def get_contacts_by_group(group_id):
    """Return contacts belonging to one group."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                contacts.id,
                contacts.name,
                contacts.phone,
                contacts.email,
                contacts.address,
                contacts.group_id,
                groups.name AS group_name
            FROM contacts
            LEFT JOIN groups ON contacts.group_id = groups.id
            WHERE contacts.group_id = ?
            ORDER BY LOWER(contacts.name), contacts.name
            """,
            (group_id,),
        )
        return _contacts_from_rows(cursor.fetchall())
    finally:
        conn.close()
