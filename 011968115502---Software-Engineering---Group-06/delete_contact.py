"""Delete-contact workflow."""

import database


def delete_contact(contact_id):
    """Delete a contact by id."""
    affected_rows = database.delete_contact(contact_id)
    if affected_rows == 0:
        raise ValueError("Contact not found.")
    return affected_rows
