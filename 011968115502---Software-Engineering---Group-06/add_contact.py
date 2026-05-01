"""Validation and add-contact workflow."""

import re

import database

PHONE_PATTERN = re.compile(r"^\d{10,11}$")
EMAIL_PATTERN = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def validate_contact(name, phone, email="", exclude_contact_id=None):
    """Validate contact fields required by the specification."""
    if not name or not name.strip():
        return False, "Contact name must not be empty."
    if not phone or not phone.strip():
        return False, "Phone number must not be empty."
    if not PHONE_PATTERN.match(phone.strip()):
        return False, "Phone number must be 10-11 digits."
    if email and not EMAIL_PATTERN.match(email.strip()):
        return False, "Invalid email format."
    if database.phone_exists(phone.strip(), exclude_contact_id=exclude_contact_id):
        return False, "Phone number already exists."
    return True, "Valid"


def normalize_contact(name, phone, email="", address="", group_id=None):
    """Trim contact fields and convert empty optional values to safe defaults."""
    clean_name = name.strip()
    clean_phone = phone.strip()
    clean_email = email.strip() if email else ""
    clean_address = address.strip() if address else ""
    clean_group_id = None if group_id in ("", None) else int(group_id)
    return clean_name, clean_phone, clean_email, clean_address, clean_group_id


def add_contact(name, phone, email="", address="", group_id=None):
    """Validate and save a new contact."""
    clean_name, clean_phone, clean_email, clean_address, clean_group_id = (
        normalize_contact(name, phone, email, address, group_id)
    )
    is_valid, message = validate_contact(clean_name, clean_phone, clean_email)
    if not is_valid:
        raise ValueError(message)

    return database.insert_contact(
        clean_name,
        clean_phone,
        clean_email,
        clean_address,
        clean_group_id,
    )
