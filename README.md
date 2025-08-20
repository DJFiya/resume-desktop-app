# Resume Builder

A Python desktop application for building, editing, organizing, and exporting professional resumes with a user-friendly interface.

## Features

- Intuitive GUI for resume creation and editing
- Add, edit, and reorder resume sections and items
- Save and load resume data to/from disk
- Export to LaTeX and PDF (if TeX is installed)
- Customizable templates (via Jinja2)

## Setup

1. **Clone the repository:**
   ```
   git clone https://github.com/yourusername/resume-builder.git
   cd resume-builder
   ```

2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

   *Dependencies include:*
   - PySimpleGUI
   - jinja2

3. **(Optional) Install a TeX distribution**  
   To enable PDF export, install a TeX distribution such as [TeX Live](https://www.tug.org/texlive/) or [MiKTeX](https://miktex.org/).

## Usage

1. **Launch the application:**
   ```
   python main.py
   ```

2. **Build your resume:**
   - Use the GUI to add and organize sections (e.g., Education, Experience).
   - Save your progress at any time.

3. **Export:**
   - Export your resume as a `.tex` file.
   - If TeX is installed, generate a PDF directly from the app.
