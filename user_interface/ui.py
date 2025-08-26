"""
Tkinter/ttk UI for the Resume Maker.
Implements the Stage 2 flow without PySimpleGUI.
- Collapsible Header
- Skills (SkillType groups)
- Experience (with bullets)
- Projects
- Education
- Reorder Sections via Up/Down
- Per-entry "Include" flags
- Save / Load JSON using models.Resume
- Export to LaTeX (stub)
"""
from __future__ import annotations

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Import your domain models & validators
try:
    from models.models import (
        Header, SkillType, SkillSection,
        BulletPoint, Experience, ExperienceSection,
        Project, ProjectSection, Education, EducationSection,
        Resume
    )
    from models.type_validator import Date, Email, GitHub, LinkedIn, PhoneNumber, Website
    from latex.converter import load_json_and_generate_latex
except Exception as e:
    # We don't crash on import so the user sees a clear message in the UI.
    Header = SkillType = SkillSection = BulletPoint = Experience = ExperienceSection = None
    Project = ProjectSection = Education = EducationSection = Resume = None
    Date = Email = GitHub = LinkedIn = PhoneNumber = Website = None
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


# -------------------------
# Utility: CollapsibleFrame
# -------------------------
class CollapsibleFrame(ttk.Frame):
    def __init__(self, master, title: str, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.columnconfigure(0, weight=1)

        self._open = tk.BooleanVar(value=True)

        self.header = ttk.Frame(self)
        self.header.grid(row=0, column=0, sticky="ew", pady=(4, 2))
        self.header.columnconfigure(1, weight=1)

        self.toggle_btn = ttk.Checkbutton(
            self.header, text="",
            variable=self._open, command=self._toggle,
            style="Toolbutton"
        )
        self.toggle_btn.grid(row=0, column=0, padx=(2, 6))

        self.title_lbl = ttk.Label(self.header, text=title, font=("", 11, "bold"))
        self.title_lbl.grid(row=0, column=1, sticky="w")

        self.body = ttk.Frame(self)
        self.body.grid(row=1, column=0, sticky="ew")

    def _toggle(self):
        if self._open.get():
            self.body.grid()
        else:
            self.body.grid_remove()


# -------------------------
# Entry Rendering helpers
# -------------------------
def _prefix_included(label: str, included: bool) -> str:
    return f"[✓] {label}" if included else f"[ ] {label}"


def _ask_yes_no(title: str, text: str) -> bool:
    return messagebox.askyesno(title, text)


# -------------------------
# Dialogs (modal Toplevels)
# -------------------------
class SkillTypeDialog(tk.Toplevel):
    """Create/Edit a SkillType (name + list of skills)."""
    def __init__(self, master, initial=None):
        super().__init__(master)
        self.title("Skill Type")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.result = None
        name = initial.get("name") if initial else ""
        skills = initial.get("skills", []) if initial else []

        frm = ttk.Frame(self, padding=10)
        frm.grid(sticky="nsew")
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar(value=name)
        ttk.Entry(frm, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="ew")

        ttk.Label(frm, text="Skills (comma-separated):").grid(row=1, column=0, sticky="w", pady=(6,0))
        self.skills_var = tk.StringVar(value=", ".join(skills))
        ttk.Entry(frm, textvariable=self.skills_var, width=40).grid(row=1, column=1, sticky="ew")

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=2, pady=(10,0), sticky="e")
        ttk.Button(btns, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=(0,6))
        ttk.Button(btns, text="Save", command=self._save).grid(row=0, column=1)

        self.bind("<Return>", lambda e: self._save())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_visibility()
        self.focus_set()

    def _save(self):
        name = self.name_var.get().strip()
        skills = [s.strip() for s in self.skills_var.get().split(",") if s.strip()]
        if not name:
            messagebox.showerror("Error", "Name cannot be empty.")
            return
        if not skills:
            messagebox.showerror("Error", "Please add at least one skill.")
            return
        self.result = {"name": name, "skills": skills, "include": True}
        self.destroy()


class BulletsEditor(ttk.Frame):
    """Widget to manage bullet points list."""
    def __init__(self, master, initial=None, max_len=255):
        super().__init__(master)
        self.max_len = max_len
        self.bullets = list(initial or [])
        self.columnconfigure(0, weight=1)

        self.lst = tk.Listbox(self, height=6, activestyle="dotbox")
        self.lst.grid(row=0, column=0, sticky="nsew")
        self._refresh()

        ctrls = ttk.Frame(self)
        ctrls.grid(row=1, column=0, sticky="ew", pady=(6,0))
        ctrls.columnconfigure(1, weight=1)

        ttk.Label(ctrls, text="Bullet:").grid(row=0, column=0, sticky="w")
        self.new_var = tk.StringVar()
        ttk.Entry(ctrls, textvariable=self.new_var).grid(row=0, column=1, sticky="ew", padx=(6,6))
        ttk.Button(ctrls, text="Add", command=self.add_bullet).grid(row=0, column=2)

        bbar = ttk.Frame(self)
        bbar.grid(row=2, column=0, sticky="e", pady=(6,0))
        ttk.Button(bbar, text="Delete", command=self.delete_selected).grid(row=0, column=0, padx=(0,6))
        ttk.Button(bbar, text="Move Up", command=lambda: self.move(-1)).grid(row=0, column=1, padx=(0,6))
        ttk.Button(bbar, text="Move Down", command=lambda: self.move(1)).grid(row=0, column=2)

    def _refresh(self):
        self.lst.delete(0, tk.END)
        for b in self.bullets:
            self.lst.insert(tk.END, b)

    def add_bullet(self):
        text = self.new_var.get().strip()
        if not text:
            return
        if len(text) > self.max_len:
            messagebox.showerror("Error", f"Bullet cannot exceed {self.max_len} characters.")
            return
        self.bullets.append(text)
        self.new_var.set("")
        self._refresh()

    def delete_selected(self):
        sel = list(self.lst.curselection())
        if not sel:
            return
        for idx in reversed(sel):
            self.bullets.pop(idx)
        self._refresh()

    def move(self, delta):
        sel = list(self.lst.curselection())
        if not sel:
            return
        idx = sel[0]
        new_idx = max(0, min(len(self.bullets)-1, idx + delta))
        if new_idx == idx:
            return
        self.bullets[idx], self.bullets[new_idx] = self.bullets[new_idx], self.bullets[idx]
        self._refresh()
        self.lst.selection_set(new_idx)


class ExperienceDialog(tk.Toplevel):
    def __init__(self, master, initial=None):
        super().__init__(master)
        self.title("Experience")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.result = None

        data = initial or {}
        position = data.get("position", "")
        company = data.get("company", "")
        start = data.get("start_date", "")
        end = data.get("end_date", "")
        bullets = data.get("description", [])

        frm = ttk.Frame(self, padding=10)
        frm.grid(sticky="nsew")
        for i in range(2):
            frm.columnconfigure(i, weight=1)

        ttk.Label(frm, text="Position:").grid(row=0, column=0, sticky="w")
        self.position_var = tk.StringVar(value=position)
        ttk.Entry(frm, textvariable=self.position_var, width=40).grid(row=0, column=1, sticky="ew")

        ttk.Label(frm, text="Company:").grid(row=1, column=0, sticky="w", pady=(6,0))
        self.company_var = tk.StringVar(value=company)
        ttk.Entry(frm, textvariable=self.company_var, width=40).grid(row=1, column=1, sticky="ew")

        ttk.Label(frm, text="Start Date (e.g. 2023-06):").grid(row=2, column=0, sticky="w", pady=(6,0))
        self.start_var = tk.StringVar(value=start)
        ttk.Entry(frm, textvariable=self.start_var).grid(row=2, column=1, sticky="ew")

        ttk.Label(frm, text="End Date (YYYY-MM or 'present')").grid(row=3, column=0, sticky="w", pady=(6,0))
        self.end_var = tk.StringVar(value=end)
        ttk.Entry(frm, textvariable=self.end_var).grid(row=3, column=1, sticky="ew")

        ttk.Label(frm, text="Description bullets:").grid(row=4, column=0, columnspan=2, sticky="w", pady=(8,2))
        self.bullets = BulletsEditor(frm, initial=bullets)
        self.bullets.grid(row=5, column=0, columnspan=2, sticky="nsew")

        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=2, pady=(10,0), sticky="e")
        ttk.Button(btns, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=(0,6))
        ttk.Button(btns, text="Save", command=self._save).grid(row=0, column=1)

        self.bind("<Return>", lambda e: self._save())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_visibility()
        self.focus_set()

    def _save(self):
        position = self.position_var.get().strip()
        company = self.company_var.get().strip()
        start = self.start_var.get().strip()
        end = self.end_var.get().strip() or "present"
        bullets = list(self.bullets.bullets)

        if not position or not company:
            messagebox.showerror("Error", "Position and Company are required.")
            return
        if not bullets:
            messagebox.showerror("Error", "Please add at least one bullet.")
            return

        self.result = {
            "position": position,
            "company": company,
            "start_date": start,
            "end_date": end,
            "description": bullets,
            "include": True,
        }
        self.destroy()


class ProjectDialog(tk.Toplevel):
    def __init__(self, master, initial=None):
        super().__init__(master)
        self.title("Project")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.result = None

        data = initial or {}
        name = data.get("name", "")
        skills = data.get("skills", [])
        link = data.get("link", "")
        bullets = data.get("description", [])

        frm = ttk.Frame(self, padding=10)
        frm.grid(sticky="nsew")
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar(value=name)
        ttk.Entry(frm, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="ew")

        ttk.Label(frm, text="Skills Used (comma-separated):").grid(row=1, column=0, sticky="w", pady=(6,0))
        self.skills_var = tk.StringVar(value=", ".join(skills))
        ttk.Entry(frm, textvariable=self.skills_var).grid(row=1, column=1, sticky="ew")

        ttk.Label(frm, text="Link (optional):").grid(row=2, column=0, sticky="w", pady=(6,0))
        self.link_var = tk.StringVar(value=link)
        ttk.Entry(frm, textvariable=self.link_var).grid(row=2, column=1, sticky="ew")

        ttk.Label(frm, text="Description bullets:").grid(row=3, column=0, columnspan=2, sticky="w", pady=(8,2))
        self.bullets = BulletsEditor(frm, initial=bullets)
        self.bullets.grid(row=4, column=0, columnspan=2, sticky="nsew")

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=2, pady=(10,0), sticky="e")
        ttk.Button(btns, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=(0,6))
        ttk.Button(btns, text="Save", command=self._save).grid(row=0, column=1)

        self.bind("<Return>", lambda e: self._save())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_visibility()
        self.focus_set()

    def _save(self):
        name = self.name_var.get().strip()
        skills = [s.strip() for s in self.skills_var.get().split(",") if s.strip()]
        link = self.link_var.get().strip()
        bullets = list(self.bullets.bullets)

        if not name or not skills:
            messagebox.showerror("Error", "Name and at least one skill are required.")
            return
        if not bullets:
            messagebox.showerror("Error", "Please add at least one bullet.")
            return

        self.result = {
            "name": name,
            "skills": skills,
            "link": link or None,
            "description": bullets,
            "include": True,
        }
        self.destroy()


class AwardsEditor(ttk.Frame):
    def __init__(self, master, initial=None):
        super().__init__(master)
        self.awards = list(initial or [])
        self.columnconfigure(0, weight=1)

        self.lst = tk.Listbox(self, height=5, activestyle="dotbox")
        self.lst.grid(row=0, column=0, sticky="nsew")
        self._refresh()

        ctrls = ttk.Frame(self)
        ctrls.grid(row=1, column=0, sticky="ew", pady=(6,0))
        ctrls.columnconfigure(1, weight=1)

        ttk.Label(ctrls, text="Award:").grid(row=0, column=0, sticky="w")
        self.new_var = tk.StringVar()
        ttk.Entry(ctrls, textvariable=self.new_var).grid(row=0, column=1, sticky="ew", padx=(6,6))
        ttk.Button(ctrls, text="Add", command=self.add_item).grid(row=0, column=2)

        bbar = ttk.Frame(self)
        bbar.grid(row=2, column=0, sticky="e", pady=(6,0))
        ttk.Button(bbar, text="Delete", command=self.delete_selected).grid(row=0, column=0, padx=(0,6))
        ttk.Button(bbar, text="Move Up", command=lambda: self.move(-1)).grid(row=0, column=1, padx=(0,6))
        ttk.Button(bbar, text="Move Down", command=lambda: self.move(1)).grid(row=0, column=2)

    def _refresh(self):
        self.lst.delete(0, tk.END)
        for a in self.awards:
            self.lst.insert(tk.END, a)

    def add_item(self):
        text = self.new_var.get().strip()
        if not text:
            return
        self.awards.append(text)
        self.new_var.set("")
        self._refresh()

    def delete_selected(self):
        sel = list(self.lst.curselection())
        if not sel:
            return
        for idx in reversed(sel):
            self.awards.pop(idx)
        self._refresh()

    def move(self, delta):
        sel = list(self.lst.curselection())
        if not sel:
            return
        idx = sel[0]
        new_idx = max(0, min(len(self.awards)-1, idx + delta))
        if new_idx == idx:
            return
        self.awards[idx], self.awards[new_idx] = self.awards[new_idx], self.awards[idx]
        self._refresh()
        self.lst.selection_set(new_idx)


class EducationDialog(tk.Toplevel):
    def __init__(self, master, initial=None):
        super().__init__(master)
        self.title("Education")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.result = None

        data = initial or {}
        school = data.get("school", "")
        degree = data.get("degree", "")
        start = data.get("start_date", "")
        gpa = data.get("gpa", "")
        awards = data.get("awards", [])

        frm = ttk.Frame(self, padding=10)
        frm.grid(sticky="nsew")
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="School:").grid(row=0, column=0, sticky="w")
        self.school_var = tk.StringVar(value=school)
        ttk.Entry(frm, textvariable=self.school_var).grid(row=0, column=1, sticky="ew")

        ttk.Label(frm, text="Degree:").grid(row=1, column=0, sticky="w", pady=(6,0))
        self.degree_var = tk.StringVar(value=degree)
        ttk.Entry(frm, textvariable=self.degree_var).grid(row=1, column=1, sticky="ew")

        ttk.Label(frm, text="Start Date (e.g. 2022-09):").grid(row=2, column=0, sticky="w", pady=(6,0))
        self.start_var = tk.StringVar(value=start)
        ttk.Entry(frm, textvariable=self.start_var).grid(row=2, column=1, sticky="ew")

        ttk.Label(frm, text="GPA (0.0 - 4.0, optional):").grid(row=3, column=0, sticky="w", pady=(6,0))
        self.gpa_var = tk.StringVar(value=str(gpa) if gpa != "" and gpa is not None else "")  # show blank if None
        ttk.Entry(frm, textvariable=self.gpa_var).grid(row=3, column=1, sticky="ew")

        ttk.Label(frm, text="Awards:").grid(row=4, column=0, columnspan=2, sticky="w", pady=(8,2))
        self.awards = AwardsEditor(frm, initial=awards)
        self.awards.grid(row=5, column=0, columnspan=2, sticky="nsew")

        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=2, pady=(10,0), sticky="e")
        ttk.Button(btns, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=(0,6))
        ttk.Button(btns, text="Save", command=self._save).grid(row=0, column=1)

        self.bind("<Return>", lambda e: self._save())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_visibility()
        self.focus_set()

    def _save(self):
        school = self.school_var.get().strip()
        degree = self.degree_var.get().strip()
        start = self.start_var.get().strip()
        gpa_raw = self.gpa_var.get().strip()
        gpa = float(gpa_raw) if gpa_raw else None
        awards = list(self.awards.awards)

        if not school or not degree:
            messagebox.showerror("Error", "School and Degree are required.")
            return

        self.result = {
            "school": school,
            "degree": degree,
            "start_date": start,
            "gpa": gpa,
            "awards": awards,
            "include": True,
        }
        self.destroy()


# -------------------------
# Main Application
# -------------------------
class ResumeMakerApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.master.title("Resume Maker — Tkinter")
        self.master.geometry("1000x700")
        self.grid(sticky="nsew")
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        if _IMPORT_ERROR is not None:
            msg = ttk.Label(self, text=(
                "Error importing your models. Please ensure models.py and models/type_validator.py exist.\n"
                f"Details: {_IMPORT_ERROR}"
            ), foreground="red", wraplength=900, justify="left")
            msg.grid(sticky="nw")
            return

        # ---- Data in-memory (with 'include' flags) ----
        self.skill_types: list[dict] = []      # {name, skills[], include}
        self.experiences: list[dict] = []      # {position, company, start_date, end_date, description[], include}
        self.projects: list[dict] = []         # {name, skills[], description[], link, include}
        self.educations: list[dict] = []       # {school, degree, start_date, gpa, awards[], include}
        self.section_order = ["Header", "Skills", "Experience", "Projects", "Education"]

        # ---- Menu ----
        self._build_menu()

        # ---- Header (collapsible) ----
        header_cf = CollapsibleFrame(self, "Header Information")
        header_cf.grid(row=0, column=0, sticky="ew")
        header_cf.columnconfigure(1, weight=1)
        self._build_header(header_cf.body)

        # ---- Two-column body: left=sections, right=order + actions ----
        body = ttk.Frame(self)
        body.grid(row=1, column=0, sticky="nsew", pady=(10,0))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = ttk.Notebook(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,10))

        # Skills Tab
        self.skills_tab = ttk.Frame(left)
        self._build_skills_tab(self.skills_tab)
        left.add(self.skills_tab, text="Skills")

        # Experience Tab
        self.exp_tab = ttk.Frame(left)
        self._build_experience_tab(self.exp_tab)
        left.add(self.exp_tab, text="Experience")

        # Projects Tab
        self.proj_tab = ttk.Frame(left)
        self._build_projects_tab(self.proj_tab)
        left.add(self.proj_tab, text="Projects")

        # Education Tab
        self.edu_tab = ttk.Frame(left)
        self._build_education_tab(self.edu_tab)
        left.add(self.edu_tab, text="Education")

        # Right column: Order + Save/Load/Export
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text="Section Order").grid(row=0, column=0, sticky="w")
        self.order_list = tk.Listbox(right, height=8, activestyle="dotbox")
        self.order_list.grid(row=1, column=0, sticky="nsew")
        for s in self.section_order:
            self.order_list.insert(tk.END, s)

        btns = ttk.Frame(right)
        btns.grid(row=2, column=0, sticky="e", pady=(6,0))
        ttk.Button(btns, text="Move Up", command=lambda: self._move_section(-1)).grid(row=0, column=0, padx=(0,6))
        ttk.Button(btns, text="Move Down", command=lambda: self._move_section(1)).grid(row=0, column=1)

        # Bottom action bar
        action = ttk.Frame(self)
        action.grid(row=2, column=0, sticky="ew", pady=(10,0))
        action.columnconfigure(0, weight=1)

        ttk.Button(action, text="Save Resume (JSON)", command=self.on_save).grid(row=0, column=0, sticky="w")
        ttk.Button(action, text="Load Resume (JSON)", command=self.on_load).grid(row=0, column=1, sticky="w", padx=(10,0))
        ttk.Button(action, text="Export to LaTeX", command=self.on_export).grid(row=0, column=2, sticky="w", padx=(10,0))

    # ------------------ Menu ------------------
    def _build_menu(self):
        mbar = tk.Menu(self.master)
        filem = tk.Menu(mbar, tearoff=False)
        filem.add_command(label="Save Resume (JSON)", command=self.on_save)
        filem.add_command(label="Load Resume (JSON)", command=self.on_load)
        filem.add_separator()
        filem.add_command(label="Export to LaTeX", command=self.on_export)
        filem.add_separator()
        filem.add_command(label="Quit", command=self.master.destroy)
        mbar.add_cascade(label="File", menu=filem)
        self.master.config(menu=mbar)

    # --------------- Header UI ---------------
    def _build_header(self, parent):
        parent.columnconfigure(1, weight=1)
        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.linkedin_var = tk.StringVar()
        self.portfolio_var = tk.StringVar()
        self.github_var = tk.StringVar()

        ttk.Label(parent, text="Name:").grid(row=0, column=0, sticky="w", pady=(2,2))
        ttk.Entry(parent, textvariable=self.name_var).grid(row=0, column=1, sticky="ew")

        contact_frame = ttk.LabelFrame(parent, text="Contact")
        contact_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6,0))
        contact_frame.columnconfigure(1, weight=1)

        ttk.Label(contact_frame, text="Email:").grid(row=0, column=0, sticky="w", padx=(6,6), pady=(4,2))
        ttk.Entry(contact_frame, textvariable=self.email_var).grid(row=0, column=1, sticky="ew", padx=(0,6))

        ttk.Label(contact_frame, text="Phone:").grid(row=1, column=0, sticky="w", padx=(6,6), pady=(2,2))
        ttk.Entry(contact_frame, textvariable=self.phone_var).grid(row=1, column=1, sticky="ew", padx=(0,6))

        ttk.Label(contact_frame, text="LinkedIn:").grid(row=2, column=0, sticky="w", padx=(6,6), pady=(2,2))
        ttk.Entry(contact_frame, textvariable=self.linkedin_var).grid(row=2, column=1, sticky="ew", padx=(0,6))

        ttk.Label(contact_frame, text="Portfolio:").grid(row=3, column=0, sticky="w", padx=(6,6), pady=(2,2))
        ttk.Entry(contact_frame, textvariable=self.portfolio_var).grid(row=3, column=1, sticky="ew", padx=(0,6))

        ttk.Label(contact_frame, text="GitHub:").grid(row=4, column=0, sticky="w", padx=(6,6), pady=(2,6))
        ttk.Entry(contact_frame, textvariable=self.github_var).grid(row=4, column=1, sticky="ew", padx=(0,6), pady=(0,6))

    # --------------- Skills Tab ---------------
    def _build_skills_tab(self, tab):
        tab.columnconfigure(0, weight=1)

        top = ttk.Frame(tab)
        top.grid(row=0, column=0, sticky="ew")
        ttk.Label(top, text="Skill Types").grid(row=0, column=0, sticky="w")

        self.skills_list = tk.Listbox(tab, height=10, activestyle="dotbox")
        self.skills_list.grid(row=1, column=0, sticky="nsew", pady=(4,0))

        controls = ttk.Frame(tab)
        controls.grid(row=2, column=0, sticky="e", pady=(6,0))
        ttk.Button(controls, text="Add", command=self.add_skilltype).grid(row=0, column=0, padx=(0,6))
        ttk.Button(controls, text="Edit", command=self.edit_skilltype).grid(row=0, column=1, padx=(0,6))
        ttk.Button(controls, text="Delete", command=self.delete_skilltype).grid(row=0, column=2, padx=(0,6))
        ttk.Button(controls, text="Move Up", command=lambda: self._move_item(self.skill_types, self.skills_list, -1)).grid(row=0, column=3, padx=(0,6))
        ttk.Button(controls, text="Move Down", command=lambda: self._move_item(self.skill_types, self.skills_list, 1)).grid(row=0, column=4)

        incl_frame = ttk.Frame(tab)
        incl_frame.grid(row=3, column=0, sticky="w", pady=(6,0))
        self.skill_include_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(incl_frame, text="Include selected in this resume", variable=self.skill_include_var, command=self.toggle_skill_include).grid(row=0, column=0, sticky="w")

    # ------------- Experience Tab -------------
    def _build_experience_tab(self, tab):
        tab.columnconfigure(0, weight=1)

        ttk.Label(tab, text="Experience").grid(row=0, column=0, sticky="w")
        self.exp_list = tk.Listbox(tab, height=10, activestyle="dotbox")
        self.exp_list.grid(row=1, column=0, sticky="nsew", pady=(4,0))
        self.exp_list.bind("<<ListboxSelect>>", lambda e: self._sync_include_checkbox(self.experiences, self.exp_list, self.exp_include_var))

        controls = ttk.Frame(tab)
        controls.grid(row=2, column=0, sticky="e", pady=(6,0))
        ttk.Button(controls, text="Add", command=self.add_experience).grid(row=0, column=0, padx=(0,6))
        ttk.Button(controls, text="Edit", command=self.edit_experience).grid(row=0, column=1, padx=(0,6))
        ttk.Button(controls, text="Delete", command=self.delete_experience).grid(row=0, column=2, padx=(0,6))
        ttk.Button(controls, text="Move Up", command=lambda: self._move_item(self.experiences, self.exp_list, -1)).grid(row=0, column=3, padx=(0,6))
        ttk.Button(controls, text="Move Down", command=lambda: self._move_item(self.experiences, self.exp_list, 1)).grid(row=0, column=4)

        incl_frame = ttk.Frame(tab)
        incl_frame.grid(row=3, column=0, sticky="w", pady=(6,0))
        self.exp_include_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(incl_frame, text="Include selected in this resume", variable=self.exp_include_var, command=lambda: self._toggle_include(self.experiences, self.exp_list, self.exp_include_var)).grid(row=0, column=0, sticky="w")

    # -------------- Projects Tab --------------
    def _build_projects_tab(self, tab):
        tab.columnconfigure(0, weight=1)

        ttk.Label(tab, text="Projects").grid(row=0, column=0, sticky="w")
        self.proj_list = tk.Listbox(tab, height=10, activestyle="dotbox")
        self.proj_list.grid(row=1, column=0, sticky="nsew", pady=(4,0))
        self.proj_list.bind("<<ListboxSelect>>", lambda e: self._sync_include_checkbox(self.projects, self.proj_list, self.proj_include_var))

        controls = ttk.Frame(tab)
        controls.grid(row=2, column=0, sticky="e", pady=(6,0))
        ttk.Button(controls, text="Add", command=self.add_project).grid(row=0, column=0, padx=(0,6))
        ttk.Button(controls, text="Edit", command=self.edit_project).grid(row=0, column=1, padx=(0,6))
        ttk.Button(controls, text="Delete", command=self.delete_project).grid(row=0, column=2, padx=(0,6))
        ttk.Button(controls, text="Move Up", command=lambda: self._move_item(self.projects, self.proj_list, -1)).grid(row=0, column=3, padx=(0,6))
        ttk.Button(controls, text="Move Down", command=lambda: self._move_item(self.projects, self.proj_list, 1)).grid(row=0, column=4)

        incl_frame = ttk.Frame(tab)
        incl_frame.grid(row=3, column=0, sticky="w", pady=(6,0))
        self.proj_include_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(incl_frame, text="Include selected in this resume", variable=self.proj_include_var, command=lambda: self._toggle_include(self.projects, self.proj_list, self.proj_include_var)).grid(row=0, column=0, sticky="w")

    # -------------- Education Tab --------------
    def _build_education_tab(self, tab):
        tab.columnconfigure(0, weight=1)

        ttk.Label(tab, text="Education").grid(row=0, column=0, sticky="w")
        self.edu_list = tk.Listbox(tab, height=10, activestyle="dotbox")
        self.edu_list.grid(row=1, column=0, sticky="nsew", pady=(4,0))
        self.edu_list.bind("<<ListboxSelect>>", lambda e: self._sync_include_checkbox(self.educations, self.edu_list, self.edu_include_var))

        controls = ttk.Frame(tab)
        controls.grid(row=2, column=0, sticky="e", pady=(6,0))
        ttk.Button(controls, text="Add", command=self.add_education).grid(row=0, column=0, padx=(0,6))
        ttk.Button(controls, text="Edit", command=self.edit_education).grid(row=0, column=1, padx=(0,6))
        ttk.Button(controls, text="Delete", command=self.delete_education).grid(row=0, column=2, padx=(0,6))
        ttk.Button(controls, text="Move Up", command=lambda: self._move_item(self.educations, self.edu_list, -1)).grid(row=0, column=3, padx=(0,6))
        ttk.Button(controls, text="Move Down", command=lambda: self._move_item(self.educations, self.edu_list, 1)).grid(row=0, column=4)

        incl_frame = ttk.Frame(tab)
        incl_frame.grid(row=3, column=0, sticky="w", pady=(6,0))
        self.edu_include_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(incl_frame, text="Include selected in this resume", variable=self.edu_include_var, command=lambda: self._toggle_include(self.educations, self.edu_list, self.edu_include_var)).grid(row=0, column=0, sticky="w")

    # -------------- Skills handlers --------------
    def add_skilltype(self):
        dlg = SkillTypeDialog(self.master)
        self.wait_window(dlg)
        if dlg.result:
            self.skill_types.append(dlg.result)
            self._refresh_skills()

    def edit_skilltype(self):
        idxs = self.skills_list.curselection()
        if not idxs:
            return
        idx = idxs[0]
        initial = self.skill_types[idx]
        dlg = SkillTypeDialog(self.master, initial=initial)
        self.wait_window(dlg)
        if dlg.result:
            dlg.result["include"] = initial.get("include", True)
            self.skill_types[idx] = dlg.result
            self._refresh_skills()
            self.skills_list.selection_set(idx)

    def delete_skilltype(self):
        idxs = self.skills_list.curselection()
        if not idxs:
            return
        idx = idxs[0]
        if not _ask_yes_no("Confirm", "Delete selected skill type?"):
            return
        self.skill_types.pop(idx)
        self._refresh_skills()

    def toggle_skill_include(self):
        idxs = self.skills_list.curselection()
        if not idxs:
            return
        idx = idxs[0]
        self.skill_types[idx]["include"] = bool(self.skill_include_var.get())
        self._refresh_skills()
        self.skills_list.selection_set(idx)

    def _refresh_skills(self):
        self.skills_list.delete(0, tk.END)
        for st in self.skill_types:
            label = f"{st['name']}: {', '.join(st['skills'])}"
            self.skills_list.insert(tk.END, _prefix_included(label, st.get('include', True)))
        # sync include checkbox with current selection
        self._sync_include_checkbox(self.skill_types, self.skills_list, self.skill_include_var)

    # -------------- Experience handlers --------------
    def add_experience(self):
        dlg = ExperienceDialog(self.master)
        self.wait_window(dlg)
        if dlg.result:
            self.experiences.append(dlg.result)
            self._refresh_experiences()

    def edit_experience(self):
        idxs = self.exp_list.curselection()
        if not idxs:
            return
        idx = idxs[0]
        dlg = ExperienceDialog(self.master, initial=self.experiences[idx])
        self.wait_window(dlg)
        if dlg.result:
            dlg.result["include"] = self.experiences[idx].get("include", True)
            self.experiences[idx] = dlg.result
            self._refresh_experiences()
            self.exp_list.selection_set(idx)

    def delete_experience(self):
        idxs = self.exp_list.curselection()
        if not idxs:
            return
        idx = idxs[0]
        if not _ask_yes_no("Confirm", "Delete selected experience?"):
            return
        self.experiences.pop(idx)
        self._refresh_experiences()

    def _refresh_experiences(self):
        self.exp_list.delete(0, tk.END)
        for exp in self.experiences:
            label = f"{exp['position']} — {exp['company']} ({exp['start_date']} → {exp['end_date']})"
            self.exp_list.insert(tk.END, _prefix_included(label, exp.get('include', True)))
        self._sync_include_checkbox(self.experiences, self.exp_list, self.exp_include_var)

    # -------------- Projects handlers --------------
    def add_project(self):
        dlg = ProjectDialog(self.master)
        self.wait_window(dlg)
        if dlg.result:
            self.projects.append(dlg.result)
            self._refresh_projects()

    def edit_project(self):
        idxs = self.proj_list.curselection()
        if not idxs:
            return
        idx = idxs[0]
        dlg = ProjectDialog(self.master, initial=self.projects[idx])
        self.wait_window(dlg)
        if dlg.result:
            dlg.result["include"] = self.projects[idx].get("include", True)
            self.projects[idx] = dlg.result
            self._refresh_projects()
            self.proj_list.selection_set(idx)

    def delete_project(self):
        idxs = self.proj_list.curselection()
        if not idxs:
            return
        idx = idxs[0]
        if not _ask_yes_no("Confirm", "Delete selected project?"):
            return
        self.projects.pop(idx)
        self._refresh_projects()

    def _refresh_projects(self):
        self.proj_list.delete(0, tk.END)
        for p in self.projects:
            label = f"{p['name']} — {', '.join(p['skills'])}{' ('+p['link']+')' if p.get('link') else ''}"
            self.proj_list.insert(tk.END, _prefix_included(label, p.get('include', True)))
        self._sync_include_checkbox(self.projects, self.proj_list, self.proj_include_var)

    # -------------- Education handlers --------------
    def add_education(self):
        dlg = EducationDialog(self.master)
        self.wait_window(dlg)
        if dlg.result:
            self.educations.append(dlg.result)
            self._refresh_educations()

    def edit_education(self):
        idxs = self.edu_list.curselection()
        if not idxs:
            return
        idx = idxs[0]
        dlg = EducationDialog(self.master, initial=self.educations[idx])
        self.wait_window(dlg)
        if dlg.result:
            dlg.result["include"] = self.educations[idx].get("include", True)
            self.educations[idx] = dlg.result
            self._refresh_educations()
            self.edu_list.selection_set(idx)

    def delete_education(self):
        idxs = self.edu_list.curselection()
        if not idxs:
            return
        idx = idxs[0]
        if not _ask_yes_no("Confirm", "Delete selected education?"):
            return
        self.educations.pop(idx)
        self._refresh_educations()

    def _refresh_educations(self):
        self.edu_list.delete(0, tk.END)
        for e in self.educations:
            label = f"{e['degree']} — {e['school']} ({e['start_date']})"
            gpa = e.get("gpa")
            if gpa is not None and gpa != "":
                label += f" GPA {gpa}"
            self.edu_list.insert(tk.END, _prefix_included(label, e.get('include', True)))
        self._sync_include_checkbox(self.educations, self.edu_list, self.edu_include_var)

    # -------------- Generic handlers --------------
    def _move_item(self, items: list[dict], listbox: tk.Listbox, delta: int):
        sel = list(listbox.curselection())
        if not sel:
            return
        idx = sel[0]
        new_idx = max(0, min(len(items)-1, idx + delta))
        if new_idx == idx:
            return
        items[idx], items[new_idx] = items[new_idx], items[idx]
        self._refresh_list_for(listbox)

        listbox.selection_set(new_idx)

    def _refresh_list_for(self, listbox: tk.Listbox):
        if listbox is self.skills_list:
            self._refresh_skills()
        elif listbox is self.exp_list:
            self._refresh_experiences()
        elif listbox is self.proj_list:
            self._refresh_projects()
        elif listbox is self.edu_list:
            self._refresh_educations()

    def _sync_include_checkbox(self, items: list[dict], listbox: tk.Listbox, var: tk.BooleanVar):
        sel = list(listbox.curselection())
        if not sel:
            var.set(True)
            return
        idx = sel[0]
        var.set(bool(items[idx].get("include", True)))

    def _toggle_include(self, items: list[dict], listbox: tk.Listbox, var: tk.BooleanVar):
        sel = list(listbox.curselection())
        if not sel:
            return
        idx = sel[0]
        items[idx]["include"] = bool(var.get())
        self._refresh_list_for(listbox)
        listbox.selection_set(idx)

    def _move_section(self, delta: int):
        sel = list(self.order_list.curselection())
        if not sel:
            return
        idx = sel[0]
        new_idx = max(0, min(len(self.section_order)-1, idx + delta))
        if new_idx == idx:
            return
        self.section_order[idx], self.section_order[new_idx] = self.section_order[new_idx], self.section_order[idx]
        self.order_list.delete(0, tk.END)
        for s in self.section_order:
            self.order_list.insert(tk.END, s)
        self.order_list.selection_set(new_idx)

    # -------------- Save / Load / Export --------------
    def _build_resume_object(self) -> Resume | None:
        """Collects UI data, validates via domain model, returns a Resume object or None on error."""
        try:
            # Header
            name = self.name_var.get().strip()
            if not name:
                raise ValueError("Name is required.")
            header = Header(
                name=name,
                email=Email(self.email_var.get().strip()) if self.email_var.get().strip() else None,
                number=PhoneNumber(self.phone_var.get().strip()) if self.phone_var.get().strip() else None,
                linkedin=LinkedIn(self.linkedin_var.get().strip()) if self.linkedin_var.get().strip() else None,
                portfolio=Website(self.portfolio_var.get().strip()) if self.portfolio_var.get().strip() else None,
                github=GitHub(self.github_var.get().strip()) if self.github_var.get().strip() else None,
            )

            # Skills
            included_skilltypes = [
                SkillType(st["name"], set(st["skills"])) for st in self.skill_types if st.get("include", True)
            ]
            skills_sec = SkillSection(included_skilltypes) if included_skilltypes else None

            # Experience
            included_exps = []
            for e in self.experiences:
                if not e.get("include", True):
                    continue
                desc = [BulletPoint(t) for t in e["description"]]
                start = Date(e["start_date"])
                end = Date(e["end_date"]) if e.get("end_date") else Date("present")
                included_exps.append(Experience(
                    position=e["position"],
                    company=e["company"],
                    description=desc,
                    start_date=start,
                    end_date=end
                ))
            exp_sec = ExperienceSection(included_exps) if included_exps else None

            # Projects
            included_projs = []
            for p in self.projects:
                if not p.get("include", True):
                    continue
                desc = [BulletPoint(t) for t in p["description"]]
                link = Website(p["link"]) if p.get("link") else None
                included_projs.append(Project(
                    name=p["name"],
                    skills=p["skills"],
                    description=desc,
                    link=link
                ))
            proj_sec = ProjectSection(included_projs) if included_projs else None

            # Education
            included_edu = []
            for ed in self.educations:
                if not ed.get("include", True):
                    continue
                start = Date(ed["start_date"])
                included_edu.append(Education(
                    school=ed["school"],
                    degree=ed["degree"],
                    start_date=start,
                    awards=ed.get("awards") or [],
                    gpa=ed.get("gpa"),
                ))
            edu_sec = EducationSection(included_edu) if included_edu else None

            resume = Resume(header=header, skills=skills_sec, experience=exp_sec, projects=proj_sec, education=edu_sec)
            return resume

        except Exception as ex:
            messagebox.showerror("Validation Error", f"{ex}")
            return None

    def on_save(self):
        resume = self._build_resume_object()
        if not resume:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Resume JSON"
        )
        if not path:
            return
        try:
            # Use the domain object's serializer
            resume.save_json(path)
            messagebox.showinfo("Saved", f"Saved to {path}")
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to save: {ex}")

    def on_load(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Resume JSON"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            resume = Resume.from_dict(data)
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to load:\n{ex}")
            return

        # Populate Header
        self.name_var.set(resume.header.name or "")
        self.email_var.set(str(resume.header.email) if resume.header.email else "")
        self.phone_var.set(str(resume.header.number) if resume.header.number else "")
        self.linkedin_var.set(str(resume.header.linkedin) if resume.header.linkedin else "")
        self.portfolio_var.set(str(resume.header.portfolio) if resume.header.portfolio else "")
        self.github_var.set(str(resume.header.github) if resume.header.github else "")

        # Populate Skills
        self.skill_types = []
        if resume.skills:
            for st in resume.skills.skill_types:
                self.skill_types.append({
                    "name": st.name,
                    "skills": list(st.skills),
                    "include": True,
                })
        self._refresh_skills()

        # Populate Experience
        self.experiences = []
        if resume.experience:
            for exp in resume.experience.experiences:
                self.experiences.append({
                    "position": exp.position,
                    "company": exp.company,
                    "start_date": str(exp.start_date),
                    "end_date": str(exp.end_date),
                    "description": [bp.text for bp in exp.description],
                    "include": True,
                })
        self._refresh_experiences()

        # Populate Projects
        self.projects = []
        if resume.projects:
            for p in resume.projects.projects:
                self.projects.append({
                    "name": p.name,
                    "skills": list(p.skills),
                    "link": str(p.link) if p.link else None,
                    "description": [bp.text for bp in p.description],
                    "include": True,
                })
        self._refresh_projects()

        # Populate Education
        self.educations = []
        if resume.education:
            for ed in resume.education.educations:
                self.educations.append({
                    "school": ed.school,
                    "degree": ed.degree,
                    "start_date": str(ed.start_date),
                    "gpa": ed.gpa,
                    "awards": list(ed.awards or []),
                    "include": True,
                })
        self._refresh_educations()

        messagebox.showinfo("Loaded", f"Loaded from {path}")

    def on_export(self):
        # Ask for saved JSON file
        json_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Select Resume JSON to Export"
        )
        if not json_path:
            return

        try:
            latex_code = load_json_and_generate_latex(json_path)
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to generate LaTeX: {ex}")
            return

        # Ask where to save LaTeX file
        tex_path = filedialog.asksaveasfilename(
            defaultextension=".tex",
            filetypes=[("LaTeX files", "*.tex"), ("All files", "*.*")],
            title="Save LaTeX As"
        )
        if not tex_path:
            return

        try:
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(latex_code)
            messagebox.showinfo("Exported", f"Exported LaTeX to {tex_path}")
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to save LaTeX:\n{ex}")


# -------------------------
# Entrypoint
# -------------------------
def launch_app():
    root = tk.Tk()
    style = ttk.Style(root)
    # Use a sensible theme if available
    try:
        style.theme_use("clam")
    except:
        pass
    app = ResumeMakerApp(root)
    root.mainloop()
