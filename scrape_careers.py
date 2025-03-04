import requests
from bs4 import BeautifulSoup

def scrape_career_details(career_name):
    """Scrapes career details from Wikipedia"""
    search_url = f"https://en.wikipedia.org/wiki/{career_name.replace(' ', '_')}"

    try:
        response = requests.get(search_url)
        if response.status_code != 200:
            return "Career details not found."

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract first paragraph
        career_info = soup.find("p").get_text()
        return career_info.strip()

    except Exception as e:
        return f"Error: {str(e)}"