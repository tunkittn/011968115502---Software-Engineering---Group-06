import re

def validate_contact(name, phone, email):
    if not name or not name.strip():
        return False, "Contact name must not be empty."
    if not phone or not phone.strip():
        return False, "Phone number must not be empty."
    if not re.match(r"^\d{8,15}$", phone):
        return False, "Phone number must be 8-15 digits."
    if email and not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        return False, "Invalid email format."
    return True, "Valid"

def add_contact(cursor, name, phone, email="", address=""):
    is_valid, message = validate_contact(name, phone, email)
    if not is_valid:
        raise ValueError(message)

    query = "INSERT INTO Contacts (name, phoneNumber, email, address) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (name, phone, email, address))
