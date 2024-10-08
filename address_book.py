import pickle
from collections import UserDict
import re
from datetime import datetime
from abc import ABC, abstractmethod

# Field class
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

# Name class
class Name(Field):
    def __init__(self, value):
        if not value:
            raise ValueError("Name is required.")
        super().__init__(value)

# Phone class
class Phone(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Invalid phone number format. It must be 10 digits.")
        super().__init__(value)

    @staticmethod
    def validate(value):
        return bool(re.match(r'^\d{10}$', value))

# Birthday class
class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

# Class of recording
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        phone = Phone(phone_number)
        self.phones.append(phone)

    def remove_phone(self, phone_number):
        phone_to_remove = self.find_phone(phone_number)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)
        else:
            raise ValueError("Phone number not found.")

    def edit_phone(self, old_phone_number, new_phone_number):
        phone_to_edit = self.find_phone(old_phone_number)
        if phone_to_edit:
            self.remove_phone(old_phone_number)
            self.add_phone(new_phone_number)
        else:
            raise ValueError("Phone number not found.")

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def days_to_birthday(self):
        if self.birthday:
            today = datetime.now().date()
            next_birthday = self.birthday.value.replace(year=today.year)
            if next_birthday < today:
                next_birthday = self.birthday.value.replace(year=today.year + 1)
            return (next_birthday - today).days
        return None

    def __str__(self):
        birthday_str = f", birthday: {self.birthday.value.strftime('%d.%m.%Y')}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {'; '.join(phone.value for phone in self.phones)}{birthday_str}"

# Address book class
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError("Contact not found.")

    def get_upcoming_birthdays(self):
        upcoming_birthdays = []
        today = datetime.now().date()
        for record in self.data.values():
            days = record.days_to_birthday()
            if days is not None and 0 <= days <= 7:
                upcoming_birthdays.append({"name": record.name.value, "birthday": record.birthday.value})
        return upcoming_birthdays

    def __str__(self):
        if not self.data:
            return "Address book is empty."
        return "\n".join(str(record) for record in self.data.values())

# Abstract class for user interface
class UserInterface(ABC):
    @abstractmethod
    def display(self, message: str):
        pass

# Console interface
class ConsoleInterface(UserInterface):
    def display(self, message: str):
        print(message)

# Decorator for input exceptions
def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (IndexError, ValueError, KeyError) as e:
            return f"Error: {str(e)}"
    return wrapper

@input_error
def add_contact(args, book):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_phone(args, book):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found.")
    record.edit_phone(old_phone, new_phone)
    return "Phone number updated."

@input_error
def show_phone(args, book):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found.")
    return f"{record.name.value}: {', '.join(phone.value for phone in record.phones)}"

@input_error
def show_all_contacts(book):
    return str(book)

@input_error
def add_birthday(args, book):
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found.")
    record.add_birthday(birthday)
    return "Birthday added."

@input_error
def show_birthday(args, book):
    name, *_ = args
    record = book.find(name)
    if record is None or not record.birthday:
        raise ValueError("Birthday not found.")
    return f"{record.name.value}: {record.birthday.value.strftime('%d.%m.%Y')}"

@input_error
def birthdays(args, book):
    upcoming_birthdays = book.get_upcoming_birthdays()
    result = []
    for bday in upcoming_birthdays:
        result.append(f"{bday['name']}: {bday['birthday'].strftime('%d.%m.%Y')}")
    return "\n".join(result) if result else "No upcoming birthdays."

def parse_input(user_input):
    parts = user_input.split()
    return parts[0], parts[1:]

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)
    print("Data saved successfully.")

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        print("Save file not found. Creating a new address book.")
        return AddressBook()  # Return a new address book if the file is not found

def main():
    interface = ConsoleInterface()  # Using console interface
    book = load_data()
    interface.display("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)  # Save the data before exiting
            interface.display("Good bye!")
            break

        elif command == "hello":
            interface.display("How can I help you?")

        elif command == "add":
            interface.display(add_contact(args, book))

        elif command == "change":
            interface.display(change_phone(args, book))

        elif command == "phone":
            interface.display(show_phone(args, book))

        elif command == "all":
            interface.display(show_all_contacts(book))

        elif command == "add-birthday":
            interface.display(add_birthday(args, book))

        elif command == "show-birthday":
            interface.display(show_birthday(args, book))

        elif command == "birthdays":
            interface.display(birthdays(args, book))

        else:
            interface.display("Invalid command.")

if __name__ == "__main__":
    main()
