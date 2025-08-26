"""
latex.converter.py
Generate LaTeX code from saved JSON using the Jake Gutierrez resume template.

Notes:
  * Preamble (packages, colors, commands, margins, spacing)
  * Header center block with colored FontAwesome icons
  * \section{Skills} structure with a single \item block
  * Experience using \resumeSubheading + \resumeItemListStart/End
  * Projects using \resumeProjectHeading + item lists
  * Education using \resumeSubheading
- Icons: Projects default to \faShareSquare. Experience/Education can
  optionally include an 'icon' string (e.g., 'Train', 'Heartbeat', 'Dragon',
  'Plus', 'GraduationCap'); otherwise none is shown.
"""

from __future__ import annotations
import json
from typing import Optional

# Import your datamodel. Keep the same pathing you're already using.
# If your project uses a different import path, adjust here.
from models import models  # expects models.Resume, etc.


# -----------------------
# Template preamble (verbatim)
# -----------------------
LATEX_PREAMBLE = r"""
%-------------------------
% Resume in Latex
% Author : Jake Gutierrez  (adapted for programmatic generation)
% Based off of: https://github.com/sb2nov/resume
% License : MIT
%------------------------

\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{xcolor}
\usepackage{fontawesome5}

\input{glyphtounicode}

\definecolor{vibrantblue}{RGB}{0, 102, 204}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Margins (match user's file)
\addtolength{\oddsidemargin}{-0.6in}
\addtolength{\evensidemargin}{-0.6in}
\addtolength{\textwidth}{1.2in}
\addtolength{\topmargin}{-.6in}
\addtolength{\textheight}{1.2in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Section formatting
\titleformat{\section}{
 \vspace{-8pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-3pt}]

\pdfgentounicode=1

% Custom commands (verbatim)
\newcommand{\resumeItem}[1]{
 \item\small{
 {#1 \vspace{-2pt}} }
}
\newcommand{\resumeSubheading}[4]{
 \vspace{-1pt}\item
 \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
 \textbf{#1} & #2 \\
 \textit{\small#3} & \textit{\small #4} \\
 \end{tabular*}\vspace{-4pt}
}
\newcommand{\resumeSubSubheading}[2]{
 \item
 \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
 \textit{\small#1} & \textit{\small #2} \\
 \end{tabular*}\vspace{-4pt}
}
\newcommand{\resumeProjectHeading}[2]{
 \item
 \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
 \small#1 & #2 \\
 \end{tabular*}\vspace{-4pt}
}
\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}
\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}, itemsep=-0.25pt, topsep=0pt]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[itemsep=-0.25pt, topsep=0pt]}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-3pt}}

\begin{document}
"""

LATEX_END = r"\end{document}"


# -----------------------
# Helpers
# -----------------------
_LATEX_SPECIALS = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}

def esc(text: Optional[str]) -> str:
    """Escape LaTeX specials in plain text (NOT for raw LaTeX or URLs)."""
    if text is None:
        return ""
    out = []
    for ch in str(text):
        out.append(_LATEX_SPECIALS.get(ch, ch))
    return "".join(out)

def href(url: Optional[str], label: str, blue: bool = True) -> str:
    """Create \href{url}{label}, optionally blue label."""
    if not url:
        return esc(label)
    if blue:
        return r"\href{" + url + r"}{\textcolor{vibrantblue}{" + esc(label) + r"}}"
    return r"\href{" + url + r"}{" + esc(label) + r"}"

def fa(icon_name: Optional[str]) -> str:
    """Return a \fa<Icon> control sequence if icon_name is recognized."""
    if not icon_name:
        return ""
    # Map a few human-friendly names to FontAwesome.
    mapping = {
        "Train": r"\faTrain",
        "Heartbeat": r"\faHeartbeat",
        "Trophy": r"\faTrophy",
        "Dragon": r"\faDragon",
        "Plus": r"\faPlus",
        "GraduationCap": r"\faGraduationCap",
        "ShareSquare": r"\faShareSquare",
        "Github": r"\faGithub",
        "Linkedin": r"\faLinkedin",
        "Globe": r"\faGlobe",
        "Envelope": r"\faEnvelope",
        "Phone": r"\faPhone",
    }
    return mapping.get(icon_name, "")

def blue_icon(icon_name: Optional[str]) -> str:
    """Icon with the template's colored wrapper + tiny hspace, exactly as in sample."""
    cmd = fa(icon_name)
    if not cmd:
        return ""
    return r"{\textcolor{vibrantblue}" + cmd + r"\hspace{0.5mm}} "

def maybe_icon_from_role(role: str) -> Optional[str]:
    """Heuristic icon if none provided."""
    s = (role or "").lower()
    if "test" in s or "automation" in s: return "Train"
    if "emg" in s or "sensor" in s or "bio" in s: return "Heartbeat"
    if "hackathon" in s or "founder" in s or "lead" in s: return "Trophy"
    if "karate" in s or "martial" in s: return "Dragon"
    if "teacher" in s or "tutor" in s or "assistant" in s: return "Plus"
    return None


# -----------------------
# Section builders (match user's .tex)
# -----------------------
def _str(val: Optional[object]) -> str:
    """Convert to string, treating None as empty string."""
    if val is None:
        return ""
    return str(val)

def build_header(h: models.Header) -> str:
    parts = []
    parts.append(r"\begin{center}")
    parts.append(rf"    \textbf{{\Huge \scshape {esc(_str(h.name))}}} \\ \vspace{{4pt}}")
    parts.append(r"    \small ")

    contact_chunks = []

    if getattr(h, "email", None):
        email = _str(h.email)
        contact_chunks.append(
            r"    {\textcolor{vibrantblue}\faEnvelope \hspace{0.5mm}}"
            + "\n    "
            + href(f"mailto:{email}", email)
        )

    if getattr(h, "number", None):
        digits = _str(h.number)
        tel_url = "tel:" + "".join(ch for ch in digits if ch.isdigit() or ch == "+")
        contact_chunks.append(
            r"    {\textcolor{vibrantblue}\faPhone \hspace{0.5mm}}"
            + "\n    "
            + href(tel_url, digits)
        )

    if getattr(h, "linkedin", None):
        link = _str(h.linkedin)
        contact_chunks.append(
            r"    {\textcolor{vibrantblue}\faLinkedin \hspace{0.5mm}}"
            + "\n    "
            + href(link, "Linkedin")
        )

    if getattr(h, "portfolio", None):
        link = _str(h.portfolio)
        contact_chunks.append(
            r"    {\textcolor{vibrantblue}\faGlobe \hspace{0.5mm}}"
            + "\n    "
            + href(link, "Website")
        )

    if getattr(h, "github", None):
        link = _str(h.github)
        contact_chunks.append(
            r"    {\textcolor{vibrantblue}\faGithub \hspace{0.5mm}}"
            + "\n    "
            + href(link, "GitHub")
        )

    parts.append((" \n    $|$ \n    ").join(contact_chunks))
    parts.append(r"\end{center}")
    parts.append("")
    return "\n".join(parts)


def build_skills(skills: Optional[models.SkillsSection]) -> str:
    if not skills or not getattr(skills, "skill_types", None):
        return ""
    lines = []
    lines.append(r"\section{Skills}")
    lines.append(r" \begin{itemize}[leftmargin=0.15in, label={}]")
    # Construct the single \item with categories, each ending with \\ as per template
    inner_lines = []
    for st in skills.skill_types:
        # st.name, st.skills (iterable)
        inner_lines.append(
            rf"     \textbf{{{esc(st.name)}}}{{: {esc(', '.join(st.skills))}}} \\"
        )
    lines.append(r"    \small{\item{")
    lines.append("\n".join(inner_lines))
    lines.append(r"    }}")
    lines.append(r" ")
    lines.append(r" \end{itemize}")
    lines.append("")
    return "\n".join(lines)


def build_experience(exp: Optional[models.ExperienceSection]) -> str:
    if not exp or not getattr(exp, "experiences", None):
        return ""
    lines = []
    lines.append(r"\section{Experience}")
    lines.append("")
    lines.append(r"\resumeSubHeadingListStart")

    for e in exp.experiences:
        # e.position, e.company, e.start_date, e.end_date, e.location?, e.link? e.company_link?
        position = getattr(e, "position", "") or ""
        company = getattr(e, "company", "") or ""
        start = getattr(e, "start_date", "") or ""
        end = getattr(e, "end_date", "") or ""
        location = getattr(e, "location", "") or ""
        role_link = getattr(e, "link", None) or getattr(e, "position_link", None)
        company_link = getattr(e, "company_link", None)

        # Icon before the bolded role text
        icon = getattr(e, "icon", None) or maybe_icon_from_role(position)
        icon_prefix = blue_icon(icon)

        # Left/top: colored icon + bold role (optionally hyperlinked & colored)
        role_label = r"\textbf{" + href(role_link, position, blue=True) + r"}"
        left_top = icon_prefix + role_label

        # Right/top: dates "start -- end"
        right_top = f"{esc(start)} -- {esc(end)}".strip()

        # Left/bottom: company (hyperlinked if provided)
        left_bottom = href(company_link, company, blue=False)

        # Right/bottom: location (italicized by the macro)
        right_bottom = esc(location)

        lines.append(
            rf"\resumeSubheading{{{left_top}}}{{{right_top}}}{{{left_bottom}}}{{{right_bottom}}}"
        )

        # Bullets
        bullets = getattr(e, "description", []) or []
        if bullets:
            lines.append(r"      \resumeItemListStart")
            for bp in bullets:
                # bp may be a BulletPoint object with .text, or a plain dict/string
                text = getattr(bp, "text", bp if isinstance(bp, str) else "")
                lines.append(rf"        \resumeItem{{{esc(text)}}}")
            lines.append(r"      \resumeItemListEnd")

    lines.append(r"\resumeSubHeadingListEnd")
    lines.append("")
    return "\n".join(lines)


def build_projects(proj_sec: Optional[models.ProjectSection]) -> str:
    if not proj_sec or not getattr(proj_sec, "projects", None):
        return ""
    out = []
    out.append(r"\section{Projects}")
    out.append("")
    for p in proj_sec.projects:
        out.append(r"      \resumeSubHeadingListStart")

        name = getattr(p, "name", "") or ""
        link = getattr(p, "link", None)
        skills = ", ".join(getattr(p, "skills", []) or [])
        icon = getattr(p, "icon", None) or "ShareSquare"

        left = (
            r"{\textcolor{vibrantblue}" + fa(icon) + r" \hspace{0.5mm} "
            r"\textbf{" + href(link, name, blue=True) + r"}} "
            r"$|$ "
            r"\emph{\textbf{" + esc(skills) + r"}}"
        )

        out.append(rf"\resumeProjectHeading{{{left}}}{{}}")

        bullets = getattr(p, "description", []) or []
        if bullets:
            out.append(r"          \resumeItemListStart")
            for bp in bullets:
                text = getattr(bp, "text", bp if isinstance(bp, str) else "")
                out.append(rf"            \resumeItem{{{esc(text)}}}")
            out.append(r"          \resumeItemListEnd")
        out.append(r"    \resumeSubHeadingListEnd")
        out.append("")
    return "\n".join(out)


def build_education(edu_sec: Optional[models.EducationSection]) -> str:
    if not edu_sec or not getattr(edu_sec, "educations", None):
        return ""
    lines = []
    lines.append(r"%-----------EDUCATION-----------")
    lines.append(r"\section{Education}")
    lines.append(r"  \resumeSubHeadingListStart")

    for edu in edu_sec.educations:
        school = getattr(edu, "school", "") or ""
        school_link = getattr(edu, "school_link", None) or getattr(edu, "link", None)
        start = getattr(edu, "start_date", "") or ""
        end = getattr(edu, "end_date", None)
        when = esc(start if not end else f"{start} -- {end}")
        degree = getattr(edu, "degree", "") or ""

        gpa = getattr(edu, "gpa", None)
        awards = getattr(edu, "awards", []) or []
        location = getattr(edu, "location", "") or ""

        tail_bits = [degree] if degree else []
        if awards:
            tail_bits.append(", ".join(awards))
        if gpa not in (None, ""):
            tail_bits.append(f"{gpa} GPA" if "GPA" not in str(gpa) else str(gpa))
        third = ", ".join([t for t in tail_bits if t])

        # Left/top uses graduation-cap icon + bold colored link
        left_top = (
            r"{\textcolor{vibrantblue}\faGraduationCap\hspace{0.5mm} "
            r"\textbf{" + href(school_link, school, blue=True) + r"}}"
        )

        lines.append(
            rf"\resumeSubheading{{{left_top}}}{{{when}}}{{{esc(third)}}}{{{esc(location)}}}"
        )

    lines.append(r"  \resumeSubHeadingListEnd")
    lines.append("")
    return "\n".join(lines)


def resume_to_latex(resume: models.Resume) -> str:
    parts = [LATEX_PREAMBLE]

    # Header (centered with icons/links)
    parts.append(build_header(resume.header))

    # Skills
    parts.append(build_skills(getattr(resume, "skills", None)))

    # Experience
    parts.append(build_experience(getattr(resume, "experience", None)))

    # Projects
    parts.append(build_projects(getattr(resume, "projects", None)))

    # Education
    parts.append(build_education(getattr(resume, "education", None)))

    parts.append(LATEX_END)
    return "\n".join([p for p in parts if p])  # drop empties safely


def load_json_and_generate_latex(json_path: str) -> str:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    resume = models.Resume.from_dict(data)
    return resume_to_latex(resume)
