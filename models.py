"""Contains classes for different sections of a resume."""
from datetime import datetime

from type_validator import Date, Email, GitHub, LinkedIn, PhoneNumber, Website

class Header:
    def __init__(
            self,
            name : str,
            email : Email | None = None,
            number: PhoneNumber | None = None,
            linkedin: LinkedIn | None = None,
            portfolio: Website | None = None,
            github: GitHub | None = None,
        ):
            self.name = name
            self.email = email
            self.number = number
            self.linkedin = linkedin
            self.portfolio = portfolio
            self.github = github

class SkillType:
    def __init__(self, name: str, skills: set[str]):
        self.name = name
        if not self.skills:
            raise ValueError("Skills cannot be empty.")
        self.skills = skills

class SkillSection:
    def __init__(self, skill_types: list[SkillType]):
        self.skill_types = skill_types

class BulletPoint:
    def __init__(self, text: str):
        if not text:
            raise ValueError("Bullet point text cannot be empty.")
        if len(text) > 100:
            raise ValueError("Bullet point text cannot exceed 100 characters.")
        self.text = text

class Experience:
    def __init__(
            self,
            position: str,
            company: str,
            description: list[BulletPoint],
            start_date: Date,
            end_date: Date = "present",
        ):
            if not position or not company:
                raise ValueError("Position and company cannot be empty.")
            if not description:
                raise ValueError("Description cannot be empty.")
            if start_date.to_datetime() >= end_date.to_datetime() or start_date.to_datetime() > datetime.today():
                raise ValueError("Start date cannot be after end date or present time.")
            self.position = position
            self.company = company
            self.description = description
            self.start_date = start_date
            self.end_date = end_date

class ExperienceSection:
    def __init__(self, experiences: list[Experience]):
        if not experiences:
            raise ValueError("Experience section cannot be empty.")
        self.experiences = experiences
    
class Project:
    def __init__(
            self,
            name: str,
            skills: list[str],
            description: list[BulletPoint],
            link: Website | None = None,
        ):
            if not name or not skills:
                raise ValueError("Name and skills cannot be empty.")
            if not description:
                raise ValueError("Description cannot be empty.")
            self.name = name
            self.skills = skills
            self.description = description
            self.link = link

class ProjectSection:
    def __init__(self, projects: list[Project]):
        if not projects:
            raise ValueError("Project section cannot be empty.")
        self.projects = projects

class Education:
    def __init__(
            self,
            school: str,
            degree: str,
            start_date: Date,
            awards: list[str] | None = None,
            gpa: float | None = None,
        ):
            if not degree or not school:
                raise ValueError("Degree and school cannot be empty.")
            if start_date.to_datetime() >= datetime.today():
                raise ValueError("Start date cannot be after end date.")
            if gpa is not None and (gpa < 0.0 or gpa > 4.0):
                raise ValueError("GPA must be between 0.0 and 4.0.")
            self.degree = degree
            self.school = school
            self.start_date = start_date
            self.awards = awards or []
            self.gpa = gpa

class EducationSection:
    def __init__(self, educations: list[Education]):
        if not educations:
            raise ValueError("Education section cannot be empty.")
        self.educations = educations