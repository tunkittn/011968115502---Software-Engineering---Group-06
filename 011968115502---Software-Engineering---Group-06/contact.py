class Contact:
    def __init__(self, contact_id, name, phone_number, email="", address=""):
        self._contact_id = contact_id
        self._name = name
        self._phone_number = phone_number
        self._email = email
        self._address = address

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    def get_phone_number(self):
        return self._phone_number

    def set_phone_number(self, phone):
        self._phone_number = phone
        
    def get_email(self):
        return self._email
        
    def get_address(self):
        return self._address
