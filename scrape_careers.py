import requests
from bs4 import BeautifulSoup
import json
import re

def clean_text(text):
    """Removes citation numbers and extra spaces from Wikipedia text."""
    return re.sub(r"\[\d+\]", "", text).strip()

def scrape_wikipedia(career_name):
    """Scrapes Wikipedia for career details"""
    wiki_url = f"https://en.wikipedia.org/wiki/{career_name.replace(' ', '_')}"
    try:
        response = requests.get(wiki_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if response.status_code != 200:
            return None, None  

        soup = BeautifulSoup(response.text, "html.parser")
        # Extract first meaningful paragraph
        paragraphs = soup.find_all("p")
        career_info = ""
        for para in paragraphs:
            text = clean_text(para.get_text().strip())
            if text and not text.startswith("This article"):
                career_info = text
                break

        # Extract job roles, salary, and skills from Wikipedia infobox
        infobox = soup.find("table", {"class": "infobox"})
        job_roles, salary, skills = "Not Found", "Not Found", "Not Found"

        if infobox:
            rows = infobox.find_all("tr")
            for row in rows:
                header = row.find("th")
                data = row.find("td")
                if header and data:
                    header_text = header.get_text().strip().lower()
                    data_text = clean_text(data.get_text().strip())

                    if "occupation" in header_text or "role" in header_text:
                        job_roles = data_text
                    elif "salary" in header_text or "earnings" in header_text:
                        salary = data_text
                    elif "skills" in header_text or "competencies" in header_text:
                        skills = data_text

        return career_info, {
            "Job Roles": job_roles,
            "Salary": salary,
            "Skills Required": skills
        }

    except Exception as e:
        print(f"[Wikipedia Error] {e}")
        return None, None

def scrape_backup_sources(career_name):
    """Scrapes job roles, skills, and salaries from Indeed as a backup"""
    try:
        url = f"https://www.indeed.com/q-{career_name.replace(' ', '-')}-jobs.html"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)

        if response.status_code != 200:
            return {}

        soup = BeautifulSoup(response.text, "html.parser")
        job_roles, salary = "Not Found", "Not Found"

        job_titles = soup.find_all("h2", class_="jobTitle")
        if job_titles:
            job_roles = ", ".join([title.get_text(strip=True) for title in job_titles[:3]])

        salary_info = soup.find("div", class_="salary-snippet")
        if salary_info:
            salary = salary_info.get_text(strip=True)

        return {
            "Job Roles": job_roles,
            "Salary": salary
        }

    except Exception as e:
        print(f"[Backup Source Error] {e}")
        return {}

def generate_future_scope_and_certifications(career_name):
    """Returns predefined future scope and certifications"""
    future_scope_data = {
        "Software Engineer": "Growing demand in AI, cloud computing, and cybersecurity.",
        "Data Scientist": "High demand in healthcare, finance, and automation.",
        "Network Engineer": "Growing demand in cloud networking and cybersecurity.",
        "Cybersecurity Analyst": "Increasing threats lead to high demand in every sector.",
    }

    certifications_data = {
        "Software Engineer": ["AWS Certified Developer", "Google Professional Engineer"],
        "Data Scientist": ["IBM Data Science Certificate", "Google Data Analytics Certificate"],
        "Network Engineer": ["Cisco CCNA", "CompTIA Network+"],
        "Cybersecurity Analyst": ["CEH (Certified Ethical Hacker)", "CISSP (Certified Information Security)"],
    }

    return {
        "Future Scope": future_scope_data.get(career_name, "No reliable data available."),
        "Certifications": certifications_data.get(career_name, ["No specific certifications found."])
    }

def scrape_career_details(career_name):
    """Scrapes and combines career details from multiple sources"""
    career_info, wikipedia_data = scrape_wikipedia(career_name)

    if not career_info:
        print("[INFO] Wikipedia page not found, trying backup sources...")
        wikipedia_data = scrape_backup_sources(career_name)

    ai_generated_data = generate_future_scope_and_certifications(career_name)

    final_data = {
        "Career": career_name.capitalize(),
        "Career Overview": career_info if career_info else "No data found.",
        "Job Roles": wikipedia_data.get("Job Roles", "Not Found"),
        "Average Salary": wikipedia_data.get("Salary", "Not Found"),
        "Skills Required": wikipedia_data.get("Skills Required", "Not Found"),
        "Future Scope": ai_generated_data["Future Scope"],
        "Certifications": ai_generated_data["Certifications"]
    }

    return json.dumps(final_data, indent=4)

if __name__ == "__main__":
    career = input("Enter a career: ")
    print(scrape_career_details(career))
