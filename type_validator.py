"""Contains all validator types for special data such as email, phone numbers, etc, that are not just strings."""

from datetime import datetime
import re

class Email:
    _regex = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    def __new__(cls, value: str):
        if not cls._regex.match(value):
            raise ValueError(f"Invalid email address: {value}. Format should be similar to 'name@domain.com'")
        return str.__new__(cls, value)
    
class PhoneNumber:
    _regex = re.compile(r"^\d{10}$")
    def __new__(cls, value: str):
        if not cls._regex.match(value):
            raise ValueError(f"Invalid phone number: {value}. Should be a 10 digit number.")
        return str.__new__(cls, value)

class Website:
    _url_regex = re.compile(
        r"^(https?://)?(www\.)?[\w\-]+(\.[\w\-]+)+[/#?]?.*$"
    )
    def __new__(cls, value: str):
        if not cls._url_regex.match(value):
            raise ValueError(f"Invalid URL: {value}")
        return str.__new__(cls, value)

class LinkedIn(Website):
    def __new__(cls, value: str):
        if not value.startswith("https://www.linkedin.com/"):
            raise ValueError(f"Invalid LinkedIn URL: {value}")
        return super().__new__(cls, value)

class GitHub(Website):
    def __new__(cls, value: str):
        if not value.startswith("https://github.com/"):
            raise ValueError(f"Invalid GitHub URL: {value}")
        return super().__new__(cls, value)

class Date:
    _format = "%d-%m-%Y"
    def __new__(cls, value: str):
        if value.lower() == "present":
            return str.__new__(cls, "present")
        try:
            datetime.strptime(value, cls._format)
        except ValueError:
            raise ValueError(f"Invalid date (expected dd-mm-yyyy): {value}")
        return str.__new__(cls, value)
    
    def to_datetime(self) -> datetime:
        """Convert to datetime object; 'present' is today."""
        if self.lower() == "present":
            return datetime.today()
        return datetime.strptime(self, self._format)