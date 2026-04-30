from database import load_contacts, save_contacts

def delete_contact():
    contacts = load_contacts()

    name = input("Enter contact name to delete: ")

    for contact in contacts:
        if contact["name"].lower() == name.lower():
            contacts.remove(contact)
            save_contacts(contacts)
            print("Deleted successfully!")
            return

    print("Contact not found!")
