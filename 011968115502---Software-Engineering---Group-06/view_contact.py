def get_all_contacts(cursor):
    query = "SELECT contactID, name, phoneNumber, email, address FROM Contacts ORDER BY name ASC"
    cursor.execute(query)
    return cursor.fetchall()