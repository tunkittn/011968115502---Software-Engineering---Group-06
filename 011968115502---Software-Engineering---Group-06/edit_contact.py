"""Edit-contact workflow."""

import database
from add_contact import normalize_contact, validate_contact


def edit_contact(contact_id, name, phone, email="", address="", group_id=None):
    """Validate and update an existing contact."""
    clean_name, clean_phone, clean_email, clean_address, clean_group_id = (
        normalize_contact(name, phone, email, address, group_id)
    )
    is_valid, message = validate_contact(
        clean_name, clean_phone, clean_email, exclude_contact_id=contact_id
    )
    if not is_valid:
        raise ValueError(message)

    affected_rows = database.update_contact(
        contact_id,
        clean_name,
        clean_phone,
        clean_email,
        clean_address,
        clean_group_id,
    )
    if affected_rows == 0:
        raise ValueError("Contact not found.")
    return affected_rows
