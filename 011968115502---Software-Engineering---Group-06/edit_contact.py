from database import load_contacts, save_contacts

def edit_contact():
    contacts = load_contacts()

    name = input("Enter contact name to edit: ")

    for contact in contacts:
        if contact["name"].lower() == name.lower():
            print("Old Information:")
            print("Name:", contact["name"])
            print("Phone:", contact["phone"])

            new_phone = input("Enter new phone number: ")
            contact["phone"] = new_phone

            save_contacts(contacts)
            print("Updated successfully!")
            return

    print("Contact not found!")
