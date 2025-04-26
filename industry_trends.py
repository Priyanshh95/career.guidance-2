from pytrends.request import TrendReq
import wikipedia
import requests
from bs4 import BeautifulSoup


# Wikipedia summary function
def get_wikipedia_summary(job_title):
    try:
        return wikipedia.summary(job_title, sentences=2)
    except wikipedia.exceptions.DisambiguationError:
        return f"Multiple entries found for '{job_title}', please be more specific."
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{job_title}'."
    except Exception:
        return f"Unable to fetch Wikipedia data for '{job_title}'."


# Google Trends score function
def get_google_trend_score(job_title):
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload([job_title], timeframe='today 3-m')
        interest = pytrends.interest_over_time()
        if not interest.empty and job_title in interest.columns:
            return int(interest[job_title].iloc[-1])
        return None
    except Exception:
        return None


# Get top companies hiring for a job from Naukri
def get_top_hiring_companies(job_title):
    try:
        url = f"https://www.naukri.com/{job_title.replace(' ', '-')}-jobs"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"❌ Failed to fetch page, status code: {response.status_code}")
            return []

        # DEBUG: Print first 1000 characters of the response to inspect structure
        print("📄 Response Preview:\n", response.text[:1000])

        soup = BeautifulSoup(response.text, "html.parser")

        # Find all <a> tags that might contain company names
        company_tags = soup.find_all("a", href=True)
        companies = []

        for tag in company_tags:
            href = tag['href']
            text = tag.text.strip()
            # Heuristic: if it's a company link and has readable text
            if "company" in href and text:
                companies.append(text)

        # Remove duplicates and limit to 5
        company_list = list(dict.fromkeys(companies))[:5]
        print("📦 DEBUG: Fetched Companies →", company_list)

        return company_list

    except Exception as e:
        print("❌ Error in get_top_hiring_companies:", e)
        return []


def get_salary_from_levels_fyi(job_title):
    try:
        formatted_title = job_title.replace(" ", "-").title()
        url = f"https://www.levels.fyi/role/{formatted_title}/"

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"❌ Salary page not found for {job_title}")
            return "Not available"

        soup = BeautifulSoup(response.text, "html.parser")

        # Find salary range span
        salary_tag = soup.find("div", string=lambda text: text and "Base Salary" in text)
        if salary_tag:
            parent = salary_tag.find_parent()
            salary_value = parent.find("div", class_="css-1b3v43d")  # class might change
            if salary_value:
                return salary_value.get_text(strip=True)

        # Fallback strategy: search for $ symbols
        possible_salaries = soup.find_all(string=lambda t: "$" in t and "Base" in t)
        for s in possible_salaries:
            if "$" in s:
                return s.strip()

        return "Not available"
    except Exception as e:
        print("❌ Error fetching salary from Levels.fyi:", e)
        return "Not available"

def get_salary_from_payscale(job_title):
    try:
        search_title = job_title.lower().replace(" ", "-")
        url = f"https://www.payscale.com/research/IN/Job={search_title}"

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        salary_section = soup.find("div", class_="pay-range__value")
        if salary_section:
            return salary_section.get_text(strip=True)

        # Try alternative salary label
        alt_salary = soup.find("span", string=lambda t: t and "₹" in t)
        if alt_salary:
            return alt_salary.get_text(strip=True)

        return None
    except Exception as e:
        print("❌ Payscale error:", e)
        return None

def get_salary_data(job_title):
    # Try Levels.fyi first
    levels_salary = get_salary_from_levels_fyi(job_title)
    if levels_salary and "Not available" not in levels_salary:
        return f"{levels_salary} (from Levels.fyi)"

    # Try Payscale as fallback
    payscale_salary = get_salary_from_payscale(job_title)
    if payscale_salary:
        return f"{payscale_salary} (from Payscale)"

    return "Not available"


def get_industry_trends(job_title):
    description = get_wikipedia_summary(job_title)
    trend_score = get_google_trend_score(job_title)
    companies = get_top_hiring_companies(job_title)
    salary = get_salary_data(job_title)


    return {
        "description": description,
        "trend_score": trend_score,
        "companies": companies,
        "salary": salary
    }
