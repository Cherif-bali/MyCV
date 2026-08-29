import argparse
import html
import json
import shutil
from datetime import date, datetime
from pathlib import Path

from weasyprint import HTML


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "cv_data.json"
OUTPUT_DIR = BASE_DIR / "output"
SITE_DIR = BASE_DIR / "site"


LABELS = {
    "fr": {
        "skills": "Compétences",
        "areas": "Domaines clés",
        "education": "Formation",
        "experience": "Expérience professionnelle",
        "languages": "Langues",
        "environment": "Environnement",
        "sectors": "Secteurs",
        "years": "ans d'expérience",
        "age": "ans",
        "download": "Télécharger le CV",
        "switch": "English version",
        "about": "Profil",
        "home": "Accueil",
    },
    "en": {
        "skills": "Skills",
        "areas": "Key Areas",
        "education": "Education",
        "experience": "Professional Experience",
        "languages": "Languages",
        "environment": "Environment",
        "sectors": "Sectors",
        "years": "years of experience",
        "age": "years old",
        "download": "Download CV",
        "switch": "Version française",
        "about": "Profile",
        "home": "Home",
    },
}


DOMAIN_TRANSLATIONS = {
    "en": {
        "Méthodologies": "Methodologies",
        "Langages": "Languages",
        "Protocoles de communication": "Communication Protocols",
        "RTOS / RTK": "RTOS / RTK",
        "Outils & Debug": "Tools & Debug",
        "Modélisation & Simulation": "Modeling & Simulation",
        "IA / ML": "AI / ML",
        "Systèmes": "Systems",
        "Cycle en V": "V-Model",
    }
}


def translate(value, language):
    if isinstance(value, dict):
        return value.get(language, "")
    return value


def escape(value):
    return html.escape(str(value))


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def calculate_age(date_string):
    birth = datetime.strptime(date_string, "%d/%m/%Y").date()
    today = date.today()

    return (
        today.year
        - birth.year
        - ((today.month, today.day) < (birth.month, birth.day))
    )


def calculate_experience_years(experiences):
    today = date.today()

    intervals = []

    for experience in experiences:
        start = parse_date(experience["start_date"])

        if experience["end_date"]:
            end = parse_date(experience["end_date"])
        else:
            end = today

        intervals.append((start, end))

    intervals.sort()

    merged = []

    for start, end in intervals:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

    total_days = sum(
        (end - start).days
        for start, end in merged
    )

    return total_days / 365.2425


def build_skills(data, language):
    rows = []

    for skill in data["competences"]:
        active = "●" * skill["niveau"]
        inactive = "○" * (skill["max"] - skill["niveau"])

        rows.append(
            f"""
            <tr>
                <td>{escape(translate(skill["nom"], language))}</td>
                <td class="skill-dots">
                    {active}<span>{inactive}</span>
                </td>
            </tr>
            """
        )

    return "".join(rows)


def build_domains(data, language):
    groups = []

    for category, items in data["domaines_cles"].items():

        translated_category = category

        if language == "en":
            translated_category = DOMAIN_TRANSLATIONS["en"].get(
                category,
                category
            )

        translated_items = []

        for item in items:
            if language == "en":
                translated_items.append(
                    DOMAIN_TRANSLATIONS["en"].get(item, item)
                )
            else:
                translated_items.append(item)

        groups.append(
            f"""
            <div class="domain-group">
                <div class="domain-label">
                    {escape(translated_category)}
                </div>

                <div class="domain-value">
                    {escape(", ".join(translated_items))}
                </div>
            </div>
            """
        )

    return "".join(groups)


def build_education(data, language):
    items = []

    for education in data["education"]:
        items.append(
            f"""
            <div class="education-item">
                <div class="education-year">
                    {escape(education["annee"])}
                </div>

                <div class="education-degree">
                    {escape(translate(education["diplome"], language))}
                </div>

                <div class="education-school">
                    {escape(
                        translate(
                            education["etablissement"],
                            language
                        )
                    )}
                </div>
            </div>
            """
        )

    return "".join(items)


def build_languages(data, language):
    items = []

    for item in data["languages"]:
        items.append(
            f"""
            <div class="language-item">
                <span>
                    {escape(translate(item["name"], language))}
                </span>

                <span>
                    {escape(translate(item["level"], language))}
                </span>
            </div>
            """
        )

    return "".join(items)


def build_experiences(data, language):
    labels = LABELS[language]
    cards = []

    for experience in data["experiences"]:

        bullets = "".join(
            f"<li>{bullet}</li>"
            for bullet in experience["realisations"][language]
        )

        environment = ", ".join(
            experience["environnement"]
        )

        cards.append(
            f"""
            <article class="experience-card">

                <table class="experience-header">
                    <tr>

                        <td>
                            <div class="experience-title">
                                {escape(
                                    translate(
                                        experience["titre"],
                                        language
                                    )
                                )}
                            </div>

                            <div class="experience-company">
                                {escape(experience["entreprise"])}
                            </div>
                        </td>

                        <td class="experience-date">
                            {escape(experience["debut"])}
                            –
                            {escape(
                                translate(
                                    experience["fin"],
                                    language
                                )
                            )}
                        </td>

                    </tr>
                </table>

                <p class="experience-description">
                    {escape(
                        translate(
                            experience["description"],
                            language
                        )
                    )}
                </p>

                <ul class="experience-bullets">
                    {bullets}
                </ul>

                <div class="environment">
                    <strong>
                        {labels["environment"]}:
                    </strong>

                    {escape(environment)}
                </div>

            </article>
            """
        )

    return "".join(cards)


def build_contact(profile):
    contact = []

    if profile.get("location"):
        contact.append(profile["location"])

    if profile.get("email"):
        contact.append(profile["email"])

    if profile.get("phone"):
        contact.append(profile["phone"])

    if profile.get("linkedin"):
        contact.append(profile["linkedin"])

    return " • ".join(
        escape(item)
        for item in contact
        if item
    )


PDF_CSS = """
@page {
    size: A4;
    margin: 9mm;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #f8fafc;
    color: #1e293b;
    font-family: "DejaVu Sans", Arial, sans-serif;
    font-size: 8pt;
    line-height: 1.3;
}

table {
    border-collapse: collapse;
}

.header {
    background: #0f172a;
    color: white;
    padding: 14px 17px;
    border-radius: 8px;
    margin-bottom: 7px;
}

.header-table {
    width: 100%;
}

.name {
    font-size: 20pt;
    font-weight: 700;
}

.job-title {
    font-size: 10pt;
    color: #38bdf8;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .7px;
    margin-top: 2px;
}

.contact {
    font-size: 7pt;
    color: #cbd5e1;
    margin-top: 5px;
}

.meta {
    text-align: right;
    color: #cbd5e1;
    font-size: 7pt;
}

.meta strong {
    color: white;
}

.summary {
    background: white;
    border-left: 4px solid #0284c7;
    padding: 7px 9px;
    margin-bottom: 7px;
    font-size: 7.5pt;
}

.layout {
    width: 100%;
}

.sidebar {
    width: 29%;
    vertical-align: top;
    padding-right: 6px;
}

.content {
    width: 71%;
    vertical-align: top;
    padding-left: 5px;
}

.box {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    padding: 7px;
    margin-bottom: 7px;
}

.section-title {
    font-size: 8.5pt;
    font-weight: 700;
    text-transform: uppercase;
    border-bottom: 2px solid #0284c7;
    padding-bottom: 2px;
    margin-bottom: 5px;
}

.skills-table {
    width: 100%;
}

.skills-table td {
    font-size: 7.2pt;
    padding: 1.5px 0;
}

.skill-dots {
    text-align: right;
    color: #0284c7;
    letter-spacing: 1px;
    white-space: nowrap;
}

.skill-dots span {
    color: #cbd5e1;
}

.domain-group {
    margin-bottom: 4px;
}

.domain-label {
    color: #0284c7;
    text-transform: uppercase;
    font-weight: 700;
    font-size: 6.8pt;
}

.domain-value {
    color: #475569;
    font-size: 7pt;
}

.education-item {
    margin-bottom: 5px;
}

.education-year {
    color: #0284c7;
    font-size: 7.3pt;
    font-weight: 700;
}

.education-degree {
    font-size: 7.2pt;
    font-weight: 600;
}

.education-school {
    font-size: 6.8pt;
    color: #64748b;
}

.language-item {
    display: flex;
    justify-content: space-between;
    font-size: 7.1pt;
    padding: 1.5px 0;
}

.language-item span:last-child {
    color: #64748b;
}

.experience-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #0284c7;
    border-radius: 4px;
    padding: 7px 8px;
    margin-bottom: 6px;
    page-break-inside: avoid;
}

.experience-header {
    width: 100%;
}

.experience-title {
    font-size: 8.8pt;
    font-weight: 700;
}

.experience-company {
    color: #0284c7;
    font-weight: 700;
    font-size: 7.5pt;
}

.experience-date {
    text-align: right;
    vertical-align: top;
    color: #64748b;
    font-size: 7pt;
    white-space: nowrap;
}

.experience-description {
    font-size: 7.3pt;
    margin: 4px 0;
    text-align: justify;
}

.experience-bullets {
    margin: 2px 0 4px 12px;
    padding: 0;
}

.experience-bullets li {
    font-size: 7.2pt;
    margin-bottom: 1px;
    text-align: justify;
}

.environment {
    background: #f1f5f9;
    border-radius: 3px;
    padding: 3px 4px;
    font-size: 6.7pt;
    color: #475569;
}

.environment strong {
    color: #0f172a;
}
"""


def build_pdf_html(data, language):
    labels = LABELS[language]
    profile = data["profile"]

    age = calculate_age(profile["date_naissance"])

    years = calculate_experience_years(
        data["experiences"]
    )

    return f"""
<!DOCTYPE html>

<html lang="{language}">

<head>

<meta charset="UTF-8">

<style>
{PDF_CSS}
</style>

</head>

<body>

<header class="header">

<table class="header-table">

<tr>

<td>

<div class="name">
{escape(profile["prenom"])}
{escape(profile["nom"])}
</div>

<div class="job-title">
{escape(translate(profile["titre"], language))}
</div>

<div class="contact">
{build_contact(profile)}
</div>

</td>

<td class="meta">

<strong>
{age} {labels["age"]}
</strong>

<br>

<strong>
{years:.0f}+ {labels["years"]}
</strong>

<br>

{labels["sectors"]}:
{escape(translate(profile["secteurs"], language))}

</td>

</tr>

</table>

</header>


<div class="summary">

{escape(translate(profile["summary"], language))}

</div>


<table class="layout">

<tr>

<td class="sidebar">


<div class="box">

<div class="section-title">
{labels["skills"]}
</div>

<table class="skills-table">

{build_skills(data, language)}

</table>

</div>


<div class="box">

<div class="section-title">
{labels["areas"]}
</div>

{build_domains(data, language)}

</div>


<div class="box">

<div class="section-title">
{labels["education"]}
</div>

{build_education(data, language)}

</div>


<div class="box">

<div class="section-title">
{labels["languages"]}
</div>

{build_languages(data, language)}

</div>


</td>


<td class="content">

<div class="section-title">
{labels["experience"]}
</div>

{build_experiences(data, language)}

</td>

</tr>

</table>

</body>

</html>
"""


WEB_CSS = """
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #f8fafc;
    color: #1e293b;
    font-family: Arial, Helvetica, sans-serif;
}

.container {
    max-width: 1100px;
    margin: auto;
    padding: 30px 20px;
}

.hero {
    background: #0f172a;
    color: white;
    border-radius: 14px;
    padding: 35px;
    display: flex;
    justify-content: space-between;
    gap: 30px;
}

.hero h1 {
    margin: 0;
    font-size: 42px;
}

.hero h2 {
    margin: 8px 0;
    color: #38bdf8;
    font-size: 20px;
}

.hero p {
    color: #cbd5e1;
}

.meta {
    text-align: right;
    color: #cbd5e1;
}

.buttons {
    margin: 20px 0;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.button {
    display: inline-block;
    background: #0284c7;
    color: white;
    padding: 11px 17px;
    border-radius: 7px;
    text-decoration: none;
    font-weight: bold;
}

.button.secondary {
    background: #e2e8f0;
    color: #0f172a;
}

.section {
    background: white;
    padding: 25px;
    border-radius: 12px;
    margin-top: 20px;
    border: 1px solid #e2e8f0;
}

.section h2 {
    border-bottom: 2px solid #0284c7;
    padding-bottom: 8px;
}

.experience {
    border-left: 4px solid #0284c7;
    padding: 15px;
    margin: 20px 0;
    background: #f8fafc;
    border-radius: 6px;
}

.experience h3 {
    margin-bottom: 4px;
}

.company {
    color: #0284c7;
    font-weight: bold;
}

.date {
    color: #64748b;
}

.environment {
    background: #e2e8f0;
    padding: 8px;
    border-radius: 5px;
    font-size: 14px;
}

.skills {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
}

.skill {
    padding: 12px;
    background: #f1f5f9;
    border-radius: 7px;
}

footer {
    text-align: center;
    padding: 30px;
    color: #64748b;
}

@media (max-width: 700px) {

    .hero {
        flex-direction: column;
    }

    .meta {
        text-align: left;
    }

    .hero h1 {
        font-size: 32px;
    }
}
"""


def build_web_page(data, language):
    labels = LABELS[language]
    profile = data["profile"]

    age = calculate_age(profile["date_naissance"])

    years = calculate_experience_years(
        data["experiences"]
    )

    other_language = "en" if language == "fr" else "index"

    pdf_name = (
        f"CV_{profile['prenom']}_"
        f"{profile['nom']}_"
        f"{language.upper()}.pdf"
    )

    experiences = []

    for experience in data["experiences"]:

        bullets = "".join(
            f"<li>{bullet}</li>"
            for bullet in experience["realisations"][language]
        )

        experiences.append(
            f"""
            <div class="experience">

                <h3>
                    {escape(
                        translate(
                            experience["titre"],
                            language
                        )
                    )}
                </h3>

                <div class="company">
                    {escape(experience["entreprise"])}
                </div>

                <div class="date">
                    {escape(experience["debut"])}
                    –
                    {escape(
                        translate(
                            experience["fin"],
                            language
                        )
                    )}
                </div>

                <p>
                    {escape(
                        translate(
                            experience["description"],
                            language
                        )
                    )}
                </p>

                <ul>
                    {bullets}
                </ul>

                <div class="environment">
                    <strong>
                        {labels["environment"]}:
                    </strong>

                    {escape(
                        ", ".join(
                            experience["environnement"]
                        )
                    )}
                </div>

            </div>
            """
        )

    skills = []

    for skill in data["competences"]:

        skills.append(
            f"""
            <div class="skill">

                <strong>
                    {escape(
                        translate(
                            skill["nom"],
                            language
                        )
                    )}
                </strong>

                <div>
                    {"●" * skill["niveau"]}
                    <span style="color:#cbd5e1">
                        {"●" * (
                            skill["max"]
                            - skill["niveau"]
                        )}
                    </span>
                </div>

            </div>
            """
        )

    return f"""
<!DOCTYPE html>

<html lang="{language}">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>
{escape(profile["prenom"])}
{escape(profile["nom"])}
-
{escape(
    translate(
        profile["titre"],
        language
    )
)}
</title>

<style>
{WEB_CSS}
</style>

</head>

<body>

<div class="container">


<header class="hero">

<div>

<h1>
{escape(profile["prenom"])}
{escape(profile["nom"])}
</h1>

<h2>
{escape(
    translate(
        profile["titre"],
        language
    )
)}
</h2>

<p>
{escape(
    translate(
        profile["secteurs"],
        language
    )
)}
</p>

<p>
{build_contact(profile)}
</p>

</div>


<div class="meta">

<div>
<strong>{age}</strong>
{labels["age"]}
</div>

<div>
<strong>{years:.0f}+</strong>
{labels["years"]}
</div>

</div>

</header>


<div class="buttons">

<a class="button"
   href="pdf/{pdf_name}">
{labels["download"]}
</a>

<a class="button secondary"
   href="{other_language}.html">
{labels["switch"]}
</a>

</div>


<section class="section">

<h2>
{labels["about"]}
</h2>

<p>
{escape(
    translate(
        profile["summary"],
        language
    )
)}
</p>

</section>


<section class="section">

<h2>
{labels["experience"]}
</h2>

{"".join(experiences)}

</section>


<section class="section">

<h2>
{labels["skills"]}
</h2>

<div class="skills">

{"".join(skills)}

</div>

</section>


<footer>

Cherif BALI

</footer>


</div>

</body>

</html>
"""


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def generate_pdf(data, language):
    OUTPUT_DIR.mkdir(exist_ok=True)

    profile = data["profile"]

    filename = (
        f"CV_{profile['prenom']}_"
        f"{profile['nom']}_"
        f"{language.upper()}.pdf"
    )

    output = OUTPUT_DIR / filename

    html_content = build_pdf_html(
        data,
        language
    )

    HTML(
        string=html_content,
        base_url=str(BASE_DIR)
    ).write_pdf(str(output))

    return output


def generate_website(data, language):
    SITE_DIR.mkdir(exist_ok=True)

    html_content = build_web_page(
        data,
        language
    )

    filename = (
        "index.html"
        if language == "fr"
        else "en.html"
    )

    output = SITE_DIR / filename

    output.write_text(
        html_content,
        encoding="utf-8"
    )


def generate_all():
    data = load_data()

    OUTPUT_DIR.mkdir(exist_ok=True)
    SITE_DIR.mkdir(exist_ok=True)

    pdf_directory = SITE_DIR / "pdf"

    pdf_directory.mkdir(
        exist_ok=True
    )

    for language in ("fr", "en"):

        pdf = generate_pdf(
            data,
            language
        )

        destination = (
            pdf_directory /
            pdf.name
        )

        shutil.copy2(
            pdf,
            destination
        )

        generate_website(
            data,
            language
        )

        print(
            f"✓ Generated {language.upper()}:"
            f" {pdf}"
        )

    print()
    print("Generation complete.")
    print()
    print(f"PDFs: {OUTPUT_DIR}")
    print(f"Website: {SITE_DIR}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--lang",
        choices=("fr", "en", "both"),
        default="both"
    )

    args = parser.parse_args()

    data = load_data()

    OUTPUT_DIR.mkdir(exist_ok=True)
    SITE_DIR.mkdir(exist_ok=True)

    pdf_directory = SITE_DIR / "pdf"
    pdf_directory.mkdir(exist_ok=True)

    languages = (
        ("fr", "en")
        if args.lang == "both"
        else (args.lang,)
    )

    for language in languages:

        pdf = generate_pdf(
            data,
            language
        )

        shutil.copy2(
            pdf,
            pdf_directory / pdf.name
        )

        generate_website(
            data,
            language
        )

        print(
            f"✓ {language.upper()}: {pdf}"
        )


if __name__ == "__main__":
    main()

