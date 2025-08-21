import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pytest
from models.models import (
    Resume, Header, SkillType, SkillSection, BulletPoint,
    Experience, ExperienceSection, Project, ProjectSection,
    Education, EducationSection, Date, Email, PhoneNumber,
    GitHub, LinkedIn, Website
)

def make_sample_resume():
    header = Header(
        name="Alice Example",
        email=Email("alice@example.com"),
        number=PhoneNumber("1234567890"),
        linkedin=LinkedIn("https://www.linkedin.com/in/fake-user-alice/"),
        portfolio=Website("https://portfolio.com"),
        github=GitHub("https://github.com/fake-user-alice/")
    )

    skills = SkillSection([
        SkillType("Programming", {"Python", "C++"}),
        SkillType("Web", {"HTML", "CSS"})
    ])

    experience = ExperienceSection([
        Experience(
            position="Developer",
            company="Tech Co",
            description=[BulletPoint("Built cool stuff")],
            start_date=Date("01-01-2022"),
            end_date=Date("01-01-2023")
        )
    ])

    projects = ProjectSection([
        Project(
            name="Portfolio Site",
            skills=["React", "Tailwind"],
            description=[BulletPoint("Built personal portfolio")],
            link=Website("https://example.com")
        )
    ])

    education = EducationSection([
        Education(
            school="University X",
            degree="BSc CS",
            start_date=Date("01-09-2019"),
            awards=["Dean’s List"],
            gpa=3.9
        )
    ])

    return Resume(
        header=header,
        skills=skills,
        experience=experience,
        projects=projects,
        education=education
    )

def test_roundtrip_to_dict_and_from_dict():
    resume = make_sample_resume()
    data = resume.to_dict()
    loaded_resume = Resume.from_dict(data)
    # Convert all validator objects to strings for comparison
    def normalize(d):
        if isinstance(d, dict):
            return {k: normalize(v) for k, v in d.items()}
        if isinstance(d, list):
            return [normalize(x) for x in d]
        if hasattr(d, '__str__'):
            return str(d)
        return d
    assert normalize(loaded_resume.to_dict()) == normalize(data)

def test_empty_skill_type_raises():
    with pytest.raises(ValueError):
        SkillType("Empty", set())

def test_bullet_point_length_limit():
    too_long_text = "x" * 101
    with pytest.raises(ValueError):
        BulletPoint(too_long_text)

def test_header_optional_fields():
    header = Header(name="Bob")
    assert header.email is None
    assert header.number is None
    assert header.linkedin is None
    assert header.portfolio is None
    assert header.github is None

def test_date_present():
    d = Date("present")
    assert str(d) == "present"
    assert isinstance(d.to_datetime(), type(d.to_datetime()))

if __name__ == "__main__":
    pytest.main()
