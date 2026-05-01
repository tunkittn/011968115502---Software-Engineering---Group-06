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
                address TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_groups (
                contact_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                PRIMARY KEY (contact_id, group_id),
                FOREIGN KEY (contact_id)
                    REFERENCES contacts(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (group_id)
                    REFERENCES groups(id)
                    ON DELETE CASCADE
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
            "CREATE INDEX IF NOT EXISTS idx_contact_groups_contact ON contact_groups(contact_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_contact_groups_group ON contact_groups(group_id)"
        )
        conn.commit()
    finally:
        conn.close()


def _contacts_from_rows(rows):
    """Convert rows to contact dictionaries with list of groups."""
    result = []
    for row in rows:
        contact_dict = dict(row)
        result.append(contact_dict)
    return result


def get_all_contacts():
    """Return all contacts sorted alphabetically by name."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT
                contacts.id,
                contacts.name,
                contacts.phone,
                contacts.email,
                contacts.address
            FROM contacts
            ORDER BY LOWER(contacts.name), contacts.name
            """
        )
        contacts = _contacts_from_rows(cursor.fetchall())
        
        # Fetch groups for each contact
        for contact in contacts:
            cursor.execute(
                """
                SELECT groups.id, groups.name
                FROM groups
                INNER JOIN contact_groups ON groups.id = contact_groups.group_id
                WHERE contact_groups.contact_id = ?
                ORDER BY groups.name
                """,
                (contact['id'],)
            )
            contact['groups'] = [dict(row) for row in cursor.fetchall()]
        
        return contacts
    finally:
        conn.close()


def insert_contact(name, phone, email="", address="", group_id=None):
    """Insert a contact and return the new contact id."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO contacts (name, phone, email, address)
            VALUES (?, ?, ?, ?)
            """,
            (name, phone, email, address),
        )
        contact_id = cursor.lastrowid
        
        # If group_id is provided, add to contact_groups
        if group_id is not None:
            cursor.execute(
                "INSERT INTO contact_groups (contact_id, group_id) VALUES (?, ?)",
                (contact_id, group_id)
            )
        
        conn.commit()
        return contact_id
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
                id,
                name,
                phone,
                email,
                address
            FROM contacts
            WHERE id = ?
            """,
            (contact_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        contact = dict(row)
        
        # Fetch groups for this contact
        cursor.execute(
            """
            SELECT groups.id, groups.name
            FROM groups
            INNER JOIN contact_groups ON groups.id = contact_groups.group_id
            WHERE contact_groups.contact_id = ?
            ORDER BY groups.name
            """,
            (contact_id,)
        )
        contact['groups'] = [dict(g_row) for g_row in cursor.fetchall()]
        
        return contact
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
            SET name = ?, phone = ?, email = ?, address = ?
            WHERE id = ?
            """,
            (name, phone, email, address, contact_id),
        )
        
        # If group_id is provided, update the contact_groups relationship
        if group_id is not None:
            # Clear existing groups
            cursor.execute("DELETE FROM contact_groups WHERE contact_id = ?", (contact_id,))
            # Add new group
            cursor.execute(
                "INSERT INTO contact_groups (contact_id, group_id) VALUES (?, ?)",
                (contact_id, group_id)
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
            SELECT DISTINCT
                contacts.id,
                contacts.name,
                contacts.phone,
                contacts.email,
                contacts.address
            FROM contacts
            LEFT JOIN contact_groups ON contacts.id = contact_groups.contact_id
            LEFT JOIN groups ON contact_groups.group_id = groups.id
            WHERE contacts.name LIKE ?
               OR contacts.phone LIKE ?
               OR groups.name LIKE ?
            ORDER BY LOWER(contacts.name), contacts.name
            """,
            (pattern, pattern, pattern),
        )
        contacts = _contacts_from_rows(cursor.fetchall())
        
        # Fetch groups for each contact
        for contact in contacts:
            cursor.execute(
                """
                SELECT groups.id, groups.name
                FROM groups
                INNER JOIN contact_groups ON groups.id = contact_groups.group_id
                WHERE contact_groups.contact_id = ?
                ORDER BY groups.name
                """,
                (contact['id'],)
            )
            contact['groups'] = [dict(row) for row in cursor.fetchall()]
        
        return contacts
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
    """Delete a group. Contacts in the group are kept."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contact_groups WHERE group_id = ?", (group_id,))
        cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def assign_contact_to_group(contact_id, group_id):
    """Add a contact to a group. Does not remove from other groups."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        # Check if contact exists
        cursor.execute("SELECT id FROM contacts WHERE id = ?", (contact_id,))
        if not cursor.fetchone():
            raise ValueError("Contact not found.")
        
        # Check if group exists
        if group_id is not None:
            cursor.execute("SELECT id FROM groups WHERE id = ?", (group_id,))
            if not cursor.fetchone():
                raise ValueError("Group not found.")
        
        # Check if already assigned
        cursor.execute(
            "SELECT 1 FROM contact_groups WHERE contact_id = ? AND group_id = ?",
            (contact_id, group_id)
        )
        if cursor.fetchone():
            # Already assigned, no change needed
            return 0
        
        # Add to group
        cursor.execute(
            "INSERT INTO contact_groups (contact_id, group_id) VALUES (?, ?)",
            (contact_id, group_id)
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def remove_contact_from_group(contact_id, group_id):
    """Remove a contact from a group."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM contact_groups WHERE contact_id = ? AND group_id = ?",
            (contact_id, group_id)
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
                contacts.address
            FROM contacts
            INNER JOIN contact_groups ON contacts.id = contact_groups.contact_id
            WHERE contact_groups.group_id = ?
            ORDER BY LOWER(contacts.name), contacts.name
            """,
            (group_id,),
        )
        contacts = _contacts_from_rows(cursor.fetchall())
        
        # Fetch groups for each contact
        for contact in contacts:
            cursor.execute(
                """
                SELECT groups.id, groups.name
                FROM groups
                INNER JOIN contact_groups ON groups.id = contact_groups.group_id
                WHERE contact_groups.contact_id = ?
                ORDER BY groups.name
                """,
                (contact['id'],)
            )
            contact['groups'] = [dict(row) for row in cursor.fetchall()]
        
        return contacts
    finally:
        conn.close()
