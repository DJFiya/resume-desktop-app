from datetime import datetime
import re

class Email:
    _regex = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    
    def __init__(self, value: str):
        if not self._regex.match(value):
            raise ValueError(f"Invalid email address: {value}. Format should be similar to 'name@domain.com'")
        self.value = value

    def __str__(self):
        return self.value

class PhoneNumber:
    _regex = re.compile(r"^\d{10}$")
    
    def __init__(self, value: str):
        if not self._regex.match(value):
            raise ValueError(f"Invalid phone number: {value}. Should be a 10 digit number.")
        self.value = value

    def __str__(self):
        return self.value

class Website:
    _url_regex = re.compile(r"^(https?://)?(www\.)?[\w\-]+(\.[\w\-]+)+[/#?]?.*$")
    
    def __init__(self, value: str):
        if not self._url_regex.match(value):
            raise ValueError(f"Invalid URL: {value}")
        self.value = value

    def __str__(self):
        return self.value

class LinkedIn(Website):
    def __init__(self, value: str):
        if not value.startswith("https://www.linkedin.com/"):
            raise ValueError(f"Invalid LinkedIn URL: {value}")
        super().__init__(value)

class GitHub(Website):
    def __init__(self, value: str):
        if not value.startswith("https://github.com/"):
            raise ValueError(f"Invalid GitHub URL: {value}")
        super().__init__(value)

class Date:
    _format = "%d-%m-%Y"

    def __init__(self, value: str):
        if value.lower() == "present":
            self.value = "present"
        else:
            try:
                datetime.strptime(value, self._format)
            except ValueError:
                raise ValueError(f"Invalid date (expected dd-mm-yyyy): {value}")
            self.value = value

    def to_datetime(self) -> datetime:
        if self.value == "present":
            return datetime.today()
        return datetime.strptime(self.value, self._format)

    def __str__(self):
        return self.value
