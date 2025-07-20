# Career Recommendation System

## Overview

Career Recommendation System is a web-based platform designed to help students and job seekers discover suitable career paths based on their skills, interests, and assessment results. The system leverages machine learning, self-assessment tests, and real-world placement data to provide personalized job recommendations, industry trends, and learning roadmaps.

<img width="1416" alt="Screenshot 2025-03-06 at 7 25 34 AM" src="https://github.com/user-attachments/assets/8181287d-1e2c-492d-adb3-1c43cb175b33" />

## Features

- **User Authentication:** Secure signup and login for personalized experience.
- **Aptitude, Coding, Creativity, and Communication Tests:** Assess your skills through interactive tests.
- **Job Recommendation Engine:** Get top job roles based on your academic and assessment scores using a trained ML model.
- **Personalized Roadmaps:** Generate step-by-step learning plans tailored to your strengths and desired job role.
- **Industry Trends:** Explore current trends, salaries, and top companies for various roles.
- **Career Explorer:** Search and learn about different career options, requirements, and growth potential.
- **Placement Data:** Access real placement statistics for 2024 and 2025.
- **Company Insights:** Connect with seniors and view company profiles.
- **Dashboard:** Manage your assessments and track your progress.

## Tech Stack
- **Backend:** Python, Flask, Flask-Login, Flask-SQLAlchemy
- **Frontend:** HTML, CSS (Bootstrap, custom styles), JavaScript
- **Machine Learning:** scikit-learn, pandas, joblib
- **Database:** SQLite
- **Other:** OpenAI API, BeautifulSoup, Requests, dotenv

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd career.guidance-2
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Create a `.env` file in the root directory.
   - Add your OpenAI API key:
     ```env
     OPENAI_API_KEY=your_openai_api_key_here
     ```

5. **Run the application:**
   ```bash
   python main.py
   ```
   The app will be available at `http://localhost:5000`.

## Usage
- **Sign up** for a new account or log in with your credentials.
- Take the self-assessment tests (Aptitude, Coding, Creativity, Communication).
- Enter your scores to get personalized job recommendations.
- Explore detailed job profiles, industry trends, and company insights.
- Generate a custom learning roadmap for your chosen career.
- Track your progress and manage assessments from the dashboard.

## Data Files
- `Student Placement.csv`: Training data for the ML model.
- `static/data/2024.json` and `static/data/2025.json`: Real placement and internship data.
- `aptitude_questions.json`: Questions for the aptitude test.

## License
This project is for educational purposes.

---

For any queries or contributions, please open an issue or submit a pull request.
