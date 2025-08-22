"""Contains classes for different sections of a resume."""
from datetime import datetime
import json

from models.type_validator import Date, Email, GitHub, LinkedIn, PhoneNumber, Website

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
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": str(self.email) if self.email else None,
            "number": str(self.number) if self.number else None,
            "linkedin": str(self.linkedin) if self.linkedin else None,
            "portfolio": str(self.portfolio) if self.portfolio else None,
            "github": str(self.github) if self.github else None,
        }

class SkillType:
    def __init__(self, name: str, skills: set[str]):
        self.name = name
        if not skills:
            raise ValueError("Skills cannot be empty.")
        self.skills = skills

        def to_dict(self):
            return {"name": self.name, "skills": list(self.skills)}
    

class SkillSection:
    def __init__(self, skill_types: list[SkillType]):
        self.skill_types = skill_types
    
    def to_dict(self) -> dict:
        return {
            "skill_types": [
                {"name": st.name, "skills": list(st.skills)} for st in self.skill_types
            ]
        }

class BulletPoint:
    def __init__(self, text: str):
        if not text:
            raise ValueError("Bullet point text cannot be empty.")
        if len(text) > 255:
            raise ValueError("Bullet point text cannot exceed 255 characters.")
        self.text = text
    
    def to_dict(self) -> dict:
        return {"text": self.text}

class Experience:
    def __init__(
            self,
            position: str,
            company: str,
            description: list[BulletPoint],
            start_date: Date,
            end_date: Date | None = None,
        ):
            if not position or not company:
                raise ValueError("Position and company cannot be empty.")
            if not description:
                raise ValueError("Description cannot be empty.")
            if end_date is None:
                end_date = Date("present")
            if start_date.to_datetime() >= end_date.to_datetime() or start_date.to_datetime() > datetime.today():
                raise ValueError("Start date cannot be after end date or present time.")
            self.position = position
            self.company = company
            self.description = description
            self.start_date = start_date
            self.end_date = end_date
        
    def to_dict(self):
        return {
            "position": self.position,
            "company": self.company,
            "description": [bp.to_dict() for bp in self.description],
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
        }

class ExperienceSection:
    def __init__(self, experiences: list[Experience]):
        self.experiences = experiences
    
    def to_dict(self) -> dict:
        return {
            "experiences": [exp.to_dict() for exp in self.experiences]
        }
    
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
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "skills": self.skills,
            "description": [bp.to_dict() for bp in self.description],
            "link": str(self.link) if self.link else None,
        }

class ProjectSection:
    def __init__(self, projects: list[Project]):
        self.projects = projects
    
    def to_dict(self) -> dict:
        return {
            "projects": [project.to_dict() for project in self.projects]
        }

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
    
    def to_dict(self):
        return {
            "school": self.school,
            "degree": self.degree,
            "start_date": str(self.start_date),
            "awards": self.awards,
            "gpa": self.gpa,
        }

class EducationSection:
    def __init__(self, educations: list[Education]):
        self.educations = educations

    def to_dict(self):
        return {"educations": [edu.to_dict() for edu in self.educations]}

class Resume:
    def __init__(
            self,
            header: Header,
            skills: SkillSection | None = None,
            experience: ExperienceSection | None = None,
            projects: ProjectSection | None = None,
            education: EducationSection | None = None,
        ):
            self.header = header
            self.skills = skills
            self.experience = experience
            self.projects = projects
            self.education = education

    def to_dict(self):
        return {
            "header": self.header.to_dict(),
            "skills": self.skills.to_dict() if self.skills else None,
            "experience": self.experience.to_dict() if self.experience else None,
            "projects": self.projects.to_dict() if self.projects else None,
            "education": self.education.to_dict() if self.education else None,
        }

    def save_json(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def from_dict(cls, data: dict):
        # Header
        header_data = data.get("header", {})
        header = Header(
            name=header_data.get("name", {}),
            email=Email(header_data["email"]) if header_data.get("email") else None,
            number=PhoneNumber(header_data["number"]) if header_data.get("number") else None,
            linkedin=LinkedIn(header_data["linkedin"]) if header_data.get("linkedin") else None,
            portfolio=Website(header_data["portfolio"]) if header_data.get("portfolio") else None,
            github=GitHub(header_data["github"]) if header_data.get("github") else None,
        )

        # Skills
        skills = None
        if data.get("skills"):
            skill_types = [
                SkillType(st["name"], set(st["skills"]))
                for st in data["skills"].get("skill_types", [])
            ]
            skills = SkillSection(skill_types)

        # Experience
        experience = None
        if data.get("experience"):
            experiences = [
                Experience(
                    position=exp["position"],
                    company=exp["company"],
                    description=[BulletPoint(bp["text"]) for bp in exp.get("description", [])],
                    start_date=Date(exp["start_date"]),
                    end_date=Date(exp["end_date"]) if exp.get("end_date") else Date("present"),
                )
                for exp in data["experience"].get("experiences", [])
            ]
            experience = ExperienceSection(experiences)

        # Projects
        projects = None
        if data.get("projects"):
            project_list = [
                Project(
                    name=proj["name"],
                    skills=proj.get("skills", []),
                    description=[BulletPoint(bp["text"]) for bp in proj.get("description", [])],
                    link=Website(proj["link"]) if proj.get("link") else None,
                )
                for proj in data["projects"].get("projects", [])
            ]
            projects = ProjectSection(project_list)

        # Education
        education = None
        if data.get("education"):
            educations = [
                Education(
                    school=edu["school"],
                    degree=edu["degree"],
                    start_date=Date(edu["start_date"]),
                    awards=edu.get("awards"),
                    gpa=edu.get("gpa"),
                )
                for edu in data["education"].get("educations", [])
            ]
            education = EducationSection(educations)

        return cls(
            header=header,
            skills=skills,
            experience=experience,
            projects=projects,
            education=education,
        )
