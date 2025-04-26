from flask import Flask, render_template, request, jsonify,redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pickle
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import random
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from scrape_careers import scrape_career_details
from industry_trends import get_industry_trends
import re

from flask import Flask, render_template, request, session
import subprocess
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed to use session

questions = [
    "Reverse a string.",
    "Check if a number is a prime number.",
    "Print the first n terms of the Fibonacci series.",
    "Find the factorial of a number.",
    "Check if a number is a palindrome.",
    "Find the largest element in an array.",
    "Calculate the sum of digits of a number.",
    "Count the number of vowels in a string.",
    "Check if a number is an Armstrong number.",
    "Sort an array using Bubble Sort."
]

# Expected outputs for some questions (you can expand this based on your requirements)
expected_outputs = {
    "Reverse a string.": "gnirts",
    "Check if a number is a prime number.": "Prime",  # For example: if input is 7, output would be 'Prime'
    "Find the factorial of a number.": "120",  # For input 5
    "Check if a number is a palindrome.": "Palindrome",  # For example: input 121
    "Find the largest element in an array.": "9",  # For array [1, 9, 3]
    "Calculate the sum of digits of a number.": "15",  # For input 567
    "Count the number of vowels in a string.": "3",  # For input "hello"
    "Check if a number is an Armstrong number.": "Armstrong",  # For input 153
    "Sort an array using Bubble Sort.": "1 2 3 4 5"  # For input array [5, 4, 3, 2, 1]
}

@app.route('/coding_test', methods=['GET', 'POST'])
def coding_test():
    output = None
    code = ""
    custom_input = ""
    marks = 0
    
    # Set the question only if it's not already in the session
    if 'question' not in session:
        session['question'] = random.choice(questions)
    
    question = session['question']

    if request.method == 'POST':
        code = request.form['code']
        custom_input = request.form.get('custom_input', '')
        try:
            with open("user_code.cpp", "w") as f:
                f.write(code)

            compile_result = subprocess.run(["g++", "user_code.cpp", "-o", "user_code.out"], capture_output=True, text=True)

            if compile_result.returncode != 0:
                output = compile_result.stderr
            else:
                run_result = subprocess.run(
                    ["./user_code.out"],
                    input=custom_input.strip(),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output = run_result.stdout

                # Evaluate the output and assign marks based on correctness
                if output.strip() == expected_outputs.get(question, "").strip():
                    marks = 100
                else:
                    marks = 50  # For incorrect answers, you can assign partial marks

        except subprocess.TimeoutExpired:
            output = "⏱️ Time Limit Exceeded"
        except Exception as e:
            output = str(e)

    return render_template("coding_test.html", output=output, code=code, custom_input=custom_input, question=question, marks=marks)


app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///career_guidance.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    assessments = db.relationship('Assessment', backref='user', lazy=True)

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)

class Career(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    salary_range = db.Column(db.String(100))
    growth_potential = db.Column(db.String(50))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('signup'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('signup'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('signup'))

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

import random
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user

# Sample set of 100 questions (Store this in a JSON file for better management)
QUESTIONS_FILE = "aptitude_questions.json"

# Load all questions from JSON file
def load_questions():
    with open(QUESTIONS_FILE, "r") as f:
        return json.load(f)

@app.route('/aptitude_test', methods=['GET', 'POST'])
@login_required
def aptitude_test():
    if request.method == 'POST':
        # Retrieve stored questions from session
        selected_questions = session.get('selected_questions', [])
        if not selected_questions:
            flash("Session expired! Please retake the test.", "error")
            return redirect(url_for('aptitude_test'))

        # Extract user answers from form submission
        user_answers = request.form

        # Extract correct answers from stored questions
        correct_answers = {q["id"]: q["answer"] for q in selected_questions}

        # Compute score
        score = sum(
            10 for q_id, correct_ans in correct_answers.items()
            if user_answers.get(q_id, "").strip() == correct_ans.strip()
        )

        # Save the score in database
        new_assessment = Assessment(user_id=current_user.id, assessment_type='Aptitude Test', score=score)
        db.session.add(new_assessment)
        db.session.commit()

        flash(f"You scored {score // 10} out of 10!", "success")
        return redirect(url_for('index'))

    # GET request: Select 10 random questions and store in session
    questions = load_questions()
    selected_questions = random.sample(questions, 10)
    session['selected_questions'] = selected_questions  # Store in session for later grading

    return render_template('aptitude_test.html', questions=selected_questions)


# Load and Train ML Model (only once)
def train_model():
    df = pd.read_csv("Student Placement.csv")  # Ensure this file is uploaded
    label_encoder = LabelEncoder()
    df['Profile'] = label_encoder.fit_transform(df['Profile'])

    X = df[['DSA', 'DBMS', 'OS', 'CN', 'Mathmetics', 'Aptitute', 'Comm', 'Problem Solving', 'Creative', 'Hackathons']]
    y = df['Profile']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Save Model & Encoder
    with open('job_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('label_encoder.pkl', 'wb') as f:
        pickle.dump(label_encoder, f)

# Train Model
train_model()

@app.route('/job/<job_name>')
def job_detail(job_name):
    job_info = get_job_info(job_name)  # You’ll define this function
    return render_template("job_detail.html", job_name=job_name, job_info=job_info)

def get_job_info(job_name):
    jobs = {
        "data_scientist": {
            "title": "Data Scientist",
            "description": "Uses statistics, machine learning, and data analysis to extract insights and guide data-driven decisions.",
            "skills": ["Python", "R", "SQL", "Machine Learning", "Data Visualization", "Statistical Analysis"],
            "responsibilities": [
                "Collect, clean, and analyze large datasets",
                "Build predictive models",
                "Communicate insights via reports and visualizations"
            ],
            "education": "Bachelor’s or Master’s in CS, Stats, or related field. PhD preferred for research roles.",
            "salary": "$95,000 - $150,000 per year",
            "outlook": "Excellent, with 36% growth expected over the next decade."
        },
        "software_engineer": {
            "title": "Software Engineer",
            "description": "Designs, builds, tests, and maintains software systems.",
            "skills": ["Java", "Python", "C++", "Git", "Data Structures", "OOP"],
            "responsibilities": [
                "Develop and test software applications",
                "Collaborate with cross-functional teams",
                "Maintain and improve codebases"
            ],
            "education": "Bachelor’s in CS or related field",
            "salary": "$85,000 - $140,000 per year",
            "outlook": "22% growth expected; high demand across industries."
        },
        "web_developer": {
            "title": "Web Developer",
            "description": "Builds and maintains websites and web applications.",
            "skills": ["HTML", "CSS", "JavaScript", "React", "Node.js", "UI/UX"],
            "responsibilities": [
                "Design responsive websites",
                "Ensure performance and scalability",
                "Work with designers and backend teams"
            ],
            "education": "Degree or diploma in Web Development or CS",
            "salary": "$65,000 - $110,000 per year",
            "outlook": "13% growth as businesses expand their online presence."
        },
        "business_analyst": {
            "title": "Business Analyst",
            "description": "Analyzes business processes to identify areas for improvement.",
            "skills": ["Excel", "SQL", "Requirement Gathering", "Communication", "Problem-solving"],
            "responsibilities": [
                "Identify business needs and solutions",
                "Bridge between stakeholders and tech team",
                "Document requirements and generate reports"
            ],
            "education": "Bachelor’s in Business, IT, or related field",
            "salary": "$70,000 - $115,000 per year",
            "outlook": "Growing demand as companies pursue optimization."
        },
        "system_engineer": {
            "title": "System Engineer",
            "description": "Maintains and administers an organization’s IT systems.",
            "skills": ["Linux", "Networking", "Scripting", "Cloud Platforms"],
            "responsibilities": [
                "Install and configure software and hardware",
                "Monitor system performance",
                "Troubleshoot technical issues"
            ],
            "education": "Bachelor’s in IT or related field",
            "salary": "$75,000 - $120,000 per year",
            "outlook": "Steady demand for system operations roles."
        },
        "ai_ml_engineer": {
            "title": "AI/ML Engineer",
            "description": "Develops machine learning models and AI systems.",
            "skills": ["Python", "TensorFlow", "Pandas", "NLP", "Deep Learning"],
            "responsibilities": [
                "Build and train ML models",
                "Deploy models into production",
                "Work with data teams to gather and process data"
            ],
            "education": "Bachelor’s/Master’s in AI, ML, CS, or similar",
            "salary": "$100,000 - $160,000 per year",
            "outlook": "High growth with applications across industries."
        },
        "cloud_engineer": {
            "title": "Cloud Engineer",
            "description": "Designs and maintains cloud infrastructure and services.",
            "skills": ["AWS", "Azure", "Docker", "Kubernetes", "Terraform"],
            "responsibilities": [
                "Build and manage cloud resources",
                "Implement CI/CD pipelines",
                "Ensure high availability and security"
            ],
            "education": "Bachelor’s in IT or Cloud Certifications",
            "salary": "$90,000 - $145,000 per year",
            "outlook": "Strong outlook as cloud adoption increases."
        },
        "devops_engineer": {
            "title": "DevOps Engineer",
            "description": "Combines development and operations to streamline deployment processes.",
            "skills": ["Jenkins", "Docker", "CI/CD", "Monitoring", "Linux"],
            "responsibilities": [
                "Automate software pipelines",
                "Manage infrastructure as code",
                "Collaborate with developers and IT"
            ],
            "education": "Bachelor’s in CS or related field",
            "salary": "$95,000 - $140,000 per year",
            "outlook": "Rapidly growing demand in agile environments."
        },
        "network_engineer": {
            "title": "Network Engineer",
            "description": "Designs and manages computer networks within an organization.",
            "skills": ["Cisco", "Routing/Switching", "Firewalls", "Security"],
            "responsibilities": [
                "Set up and maintain networks",
                "Troubleshoot connectivity issues",
                "Ensure network security"
            ],
            "education": "Bachelor’s in Networking or IT",
            "salary": "$75,000 - $120,000 per year",
            "outlook": "Steady growth as infrastructure scales."
        },
        "database_administrator": {
            "title": "Database Administrator",
            "description": "Maintains and secures databases, ensuring efficient access and storage.",
            "skills": ["SQL", "Oracle", "MySQL", "Backup/Recovery", "Performance Tuning"],
            "responsibilities": [
                "Install and upgrade DB systems",
                "Monitor performance",
                "Implement security policies"
            ],
            "education": "Bachelor’s in CS or Database Certifications",
            "salary": "$80,000 - $130,000 per year",
            "outlook": "Essential role for data-driven companies."
        },
        "cybersecurity_analyst": {
            "title": "Cybersecurity Analyst",
            "description": "Protects systems from cyber threats and vulnerabilities.",
            "skills": ["Firewalls", "Threat Detection", "Risk Management", "SIEM"],
            "responsibilities": [
                "Monitor and secure networks",
                "Analyze threat intelligence",
                "Respond to security incidents"
            ],
            "education": "Bachelor’s in Cybersecurity or CS",
            "salary": "$85,000 - $135,000 per year",
            "outlook": "35% growth expected due to rising cyber threats."
        },
    }
    return jobs.get(job_name.lower().replace(" ", "_"), {
        "title": "Unknown Role",
        "description": "No details found for this job role.",
        "skills": [],
        "responsibilities": [],
        "education": "N/A",
        "salary": "N/A",
        "outlook": "N/A"
    })

@app.route('/roadmap/<job_role>', methods=['GET'])
def show_roadmap(job_role):
    roadmaps = {
        'data scientist': {
            'step_1': {'task': 'Learn Python & Statistics', 'weeks': 6, 'resources': ['Coursera: Python for Data Science', 'Khan Academy: Statistics', 'DataCamp']},
            'step_2': {'task': 'Master Data Analysis & Visualization', 'weeks': 8, 'resources': ['Pandas Documentation', 'Matplotlib Tutorials', 'Tableau Public']},
            'step_3': {'task': 'Study Machine Learning Algorithms', 'weeks': 10, 'resources': ['Scikit-learn Documentation', 'Andrew Ng\'s ML Course', 'Kaggle Competitions']},
            'step_4': {'task': 'Learn Deep Learning Fundamentals', 'weeks': 8, 'resources': ['TensorFlow Tutorials', 'fast.ai Course', 'Deep Learning Specialization']},
            'step_5': {'task': 'Work on Real-World Data Projects', 'weeks': 12, 'resources': ['GitHub Repositories', 'Kaggle Datasets', 'Company Data Challenges']}
        },
        
        'software engineer': {
            'step_1': {'task': 'Master Programming Fundamentals', 'weeks': 6, 'resources': ['freeCodeCamp', 'Codecademy', 'LeetCode']},
            'step_2': {'task': 'Learn Data Structures & Algorithms', 'weeks': 8, 'resources': ['AlgoExpert', 'Introduction to Algorithms (Book)', 'HackerRank']},
            'step_3': {'task': 'Study System Design & Architecture', 'weeks': 6, 'resources': ['System Design Primer (GitHub)', 'Grokking System Design', 'AWS Architecture Blog']},
            'step_4': {'task': 'Learn Version Control & CI/CD', 'weeks': 4, 'resources': ['Git Documentation', 'GitHub Learning Lab', 'Jenkins Tutorials']},
            'step_5': {'task': 'Build Portfolio Projects', 'weeks': 10, 'resources': ['GitHub', 'Portfolio Websites', 'Open Source Contributions']}
        },
        
        'ux designer': {
            'step_1': {'task': 'Learn UI/UX Fundamentals', 'weeks': 4, 'resources': ['Interaction Design Foundation', 'Nielsen Norman Group Articles', 'UX Design Institute']},
            'step_2': {'task': 'Master Design Tools (Figma, Adobe XD)', 'weeks': 6, 'resources': ['Figma Tutorials', 'Adobe XD Learning Resources', 'Design Tool YouTube Channels']},
            'step_3': {'task': 'Practice Wireframing & Prototyping', 'weeks': 5, 'resources': ['SketchApp Resources', 'Balsamiq Tutorials', 'Dribbble Inspiration']},
            'step_4': {'task': 'Learn User Research Methods', 'weeks': 4, 'resources': ['UX Research Field Guide', 'User Testing Tools', 'Survey Design Best Practices']},
            'step_5': {'task': 'Build a Design Portfolio', 'weeks': 6, 'resources': ['Behance', 'Dribbble', 'Portfolio Website Templates']}
        },
        
        'web developer': {
            'step_1': {'task': 'Learn HTML, CSS, and JavaScript', 'weeks': 5, 'resources': ['MDN Web Docs', 'W3Schools', 'freeCodeCamp']},
            'step_2': {'task': 'Master Frontend Frameworks (React, Vue)', 'weeks': 6, 'resources': ['React Documentation', 'Vue.js Guide', 'Frontend Masters']},
            'step_3': {'task': 'Learn Backend Technologies (Node.js, Django)', 'weeks': 7, 'resources': ['Node.js Documentation', 'Django Project', 'Backend API Design']},
            'step_4': {'task': 'Study Database Design & Management', 'weeks': 5, 'resources': ['MongoDB University', 'PostgreSQL Tutorials', 'SQL Exercises']},
            'step_5': {'task': 'Deploy & Manage Web Applications', 'weeks': 4, 'resources': ['Netlify', 'Vercel Documentation', 'AWS Deployment Guides']}
        },
        
        'digital marketer': {
            'step_1': {'task': 'Learn SEO and SEM Fundamentals', 'weeks': 4, 'resources': ['Google Digital Garage', 'Moz SEO Course', 'SEMrush Academy']},
            'step_2': {'task': 'Master Social Media Marketing', 'weeks': 5, 'resources': ['Hootsuite Academy', 'Facebook Blueprint', 'Social Media Examiner']},
            'step_3': {'task': 'Study Content Marketing', 'weeks': 4, 'resources': ['Content Marketing Institute', 'HubSpot Academy', 'Copywriting Books']},
            'step_4': {'task': 'Learn Analytics Tools & Data Analysis', 'weeks': 6, 'resources': ['Google Analytics Academy', 'Tableau for Marketing', 'Data Studio']},
            'step_5': {'task': 'Execute Marketing Campaigns', 'weeks': 8, 'resources': ['A/B Testing Tools', 'Campaign Strategy Templates', 'Marketing Measurement']}
        },
        
        'product manager': {
            'step_1': {'task': 'Learn Product Management Fundamentals', 'weeks': 4, 'resources': ['Product School', 'Mind the Product', 'PM Reading Lists']},
            'step_2': {'task': 'Master User Research & Customer Development', 'weeks': 5, 'resources': ['User Interview Techniques', 'Survey Tools', 'Jobs-to-be-Done Framework']},
            'step_3': {'task': 'Study Product Strategy & Roadmapping', 'weeks': 6, 'resources': ['Roadmap Templates', 'Product Strategy Books', 'Prioritization Frameworks']},
            'step_4': {'task': 'Learn Agile & Product Development Processes', 'weeks': 5, 'resources': ['Scrum Guide', 'Agile Alliance Resources', 'Jira Tutorials']},
            'step_5': {'task': 'Build Product Management Portfolio', 'weeks': 8, 'resources': ['Case Studies', 'Product Analytics', 'Product Launch Templates']}
        },
        
        'data analyst': {
            'step_1': {'task': 'Learn SQL & Database Fundamentals', 'weeks': 5, 'resources': ['Mode Analytics SQL Tutorial', 'W3Schools SQL', 'PostgreSQL Exercises']},
            'step_2': {'task': 'Master Data Analysis Tools (Excel, Python)', 'weeks': 6, 'resources': ['Excel Data Analysis Course', 'Pandas Documentation', 'NumPy Tutorials']},
            'step_3': {'task': 'Study Data Visualization', 'weeks': 5, 'resources': ['Tableau Public', 'Power BI Learning', 'Data Visualization Best Practices']},
            'step_4': {'task': 'Learn Statistical Analysis', 'weeks': 6, 'resources': ['Khan Academy Statistics', 'StatQuest YouTube Channel', 'R for Statistical Analysis']},
            'step_5': {'task': 'Work on Data Analysis Projects', 'weeks': 8, 'resources': ['Kaggle Datasets', 'Public Data Resources', 'Data Analysis Portfolio']}
        },
        
        'cybersecurity analyst': {
            'step_1': {'task': 'Learn Network & Security Fundamentals', 'weeks': 6, 'resources': ['CompTIA Security+ Materials', 'Cybrary Courses', 'Networking Basics']},
            'step_2': {'task': 'Master Operating System Security', 'weeks': 5, 'resources': ['Linux Security Administration', 'Windows Security', 'OS Hardening Guidelines']},
            'step_3': {'task': 'Study Threat Detection & Analysis', 'weeks': 7, 'resources': ['SANS Reading Room', 'Malware Analysis Tutorials', 'Threat Intelligence Resources']},
            'step_4': {'task': 'Learn Security Tools & SIEM', 'weeks': 6, 'resources': ['Splunk Fundamentals', 'Wireshark Tutorials', 'Security Onion']},
            'step_5': {'task': 'Practice with CTFs & Security Labs', 'weeks': 8, 'resources': ['TryHackMe', 'HackTheBox', 'VulnHub']}
        },
        
        'business analyst': {
            'step_1': {'task': 'Learn Business Analysis Fundamentals', 'weeks': 4, 'resources': ['BABOK Guide', 'BA Blogs', 'Business Analysis Courses']},
            'step_2': {'task': 'Master Requirements Gathering & Documentation', 'weeks': 5, 'resources': ['User Story Templates', 'Requirements Workshops', 'Documentation Tools']},
            'step_3': {'task': 'Study Process Modeling & Analysis', 'weeks': 6, 'resources': ['BPMN Tutorials', 'Process Mapping Tools', 'System Analysis Methods']},
            'step_4': {'task': 'Learn Data Analysis for Business', 'weeks': 5, 'resources': ['Excel for BA', 'SQL for Business', 'Tableau for Analysis']},
            'step_5': {'task': 'Practice with Case Studies & Projects', 'weeks': 8, 'resources': ['BA Case Studies', 'Business Problem Solving', 'Industry Analysis']}
        },
        
        'project manager': {
            'step_1': {'task': 'Learn Project Management Fundamentals', 'weeks': 5, 'resources': ['PMBOK Guide', 'PMI Resources', 'Project Management Courses']},
            'step_2': {'task': 'Master Planning & Scheduling Techniques', 'weeks': 4, 'resources': ['Gantt Chart Tools', 'Critical Path Method', 'Project Planning Templates']},
            'step_3': {'task': 'Study Risk Management & Mitigation', 'weeks': 4, 'resources': ['Risk Register Templates', 'Risk Analysis Methods', 'Contingency Planning']},
            'step_4': {'task': 'Learn Team Leadership & Communication', 'weeks': 5, 'resources': ['Leadership Books', 'Conflict Resolution', 'Communication Frameworks']},
            'step_5': {'task': 'Practice with Project Management Tools', 'weeks': 6, 'resources': ['MS Project', 'Jira', 'Asana', 'Project Documentation Templates']}
        },
        
        'marketing manager': {
            'step_1': {'task': 'Learn Marketing Strategy & Planning', 'weeks': 5, 'resources': ['Marketing Plan Templates', 'Strategic Marketing Books', 'Industry Reports']},
            'step_2': {'task': 'Master Digital Marketing Channels', 'weeks': 6, 'resources': ['Google Digital Marketing Course', 'HubSpot Academy', 'Social Media Strategy']},
            'step_3': {'task': 'Study Brand Management', 'weeks': 4, 'resources': ['Brand Strategy Resources', 'Brand Style Guides', 'Positioning Templates']},
            'step_4': {'task': 'Learn Marketing Analytics', 'weeks': 5, 'resources': ['Google Analytics', 'Marketing Attribution Models', 'ROI Calculation']},
            'step_5': {'task': 'Practice Campaign Management', 'weeks': 8, 'resources': ['Campaign Planning Tools', 'Marketing Calendar Templates', 'Marketing Automation']}
        },
        
        'machine learning engineer': {
            'step_1': {'task': 'Master Programming & Mathematics', 'weeks': 8, 'resources': ['Advanced Python', 'Linear Algebra', 'Calculus', 'Probability']},
            'step_2': {'task': 'Learn Machine Learning Algorithms', 'weeks': 10, 'resources': ['Machine Learning Course', 'scikit-learn', 'ML Textbooks']},
            'step_3': {'task': 'Study Deep Learning Frameworks', 'weeks': 8, 'resources': ['TensorFlow', 'PyTorch', 'Deep Learning Course']},
            'step_4': {'task': 'Learn MLOps & Deployment', 'weeks': 6, 'resources': ['Docker', 'Kubernetes', 'ML Pipelines', 'Model Serving']},
            'step_5': {'task': 'Build End-to-End ML Projects', 'weeks': 10, 'resources': ['Kaggle Competitions', 'GitHub ML Projects', 'Research Papers Implementation']}
        },
        
        'frontend developer': {
            'step_1': {'task': 'Learn HTML, CSS, and JavaScript Deeply', 'weeks': 6, 'resources': ['Frontend Masters', 'CSS Tricks', 'JavaScript.info']},
            'step_2': {'task': 'Master Modern JavaScript Frameworks', 'weeks': 8, 'resources': ['React Documentation', 'Vue.js Guide', 'Angular Tutorials']},
            'step_3': {'task': 'Study Responsive Design & Accessibility', 'weeks': 4, 'resources': ['MDN Accessibility Guide', 'Responsive Web Design', 'WCAG Standards']},
            'step_4': {'task': 'Learn State Management & API Integration', 'weeks': 5, 'resources': ['Redux Documentation', 'GraphQL Tutorials', 'RESTful API Design']},
            'step_5': {'task': 'Build Complex Frontend Applications', 'weeks': 8, 'resources': ['Frontend Projects', 'UI Component Libraries', 'Animation Libraries']}
        },
        
        'backend developer': {
            'step_1': {'task': 'Learn Server-Side Programming', 'weeks': 6, 'resources': ['Node.js', 'Python Django/Flask', 'Java Spring']},
            'step_2': {'task': 'Master Database Design & Management', 'weeks': 7, 'resources': ['SQL Tutorials', 'MongoDB University', 'Database Design Principles']},
            'step_3': {'task': 'Study API Development', 'weeks': 5, 'resources': ['RESTful API Design', 'GraphQL', 'API Authentication & Security']},
            'step_4': {'task': 'Learn Server Infrastructure & Deployment', 'weeks': 6, 'resources': ['Docker', 'AWS Services', 'Nginx Configuration']},
            'step_5': {'task': 'Build Scalable Backend Services', 'weeks': 8, 'resources': ['Microservices Architecture', 'Load Balancing', 'Caching Strategies']}
        },
        
        'devops engineer': {
            'step_1': {'task': 'Learn Linux & Command Line', 'weeks': 5, 'resources': ['Linux Journey', 'Bash Scripting', 'System Administration']},
            'step_2': {'task': 'Master CI/CD Pipelines', 'weeks': 6, 'resources': ['Jenkins', 'GitHub Actions', 'GitLab CI', 'Deployment Strategies']},
            'step_3': {'task': 'Study Containerization & Orchestration', 'weeks': 7, 'resources': ['Docker Documentation', 'Kubernetes Basics', 'Container Security']},
            'step_4': {'task': 'Learn Infrastructure as Code', 'weeks': 6, 'resources': ['Terraform', 'Ansible', 'CloudFormation', 'Pulumi']},
            'step_5': {'task': 'Practice Cloud Solutions & Monitoring', 'weeks': 8, 'resources': ['AWS/Azure/GCP Services', 'Prometheus', 'Grafana', 'ELK Stack']}
        }
    }
    
    # Normalize the job role (convert to lowercase and handle common variations)
    normalized_job_role = job_role.lower()
    
    # Map variations to standard roles
    role_mapping = {
        'data scientist': 'data scientist',
        'data science': 'data scientist',
        'ds': 'data scientist',
        
        'software engineer': 'software engineer',
        'swe': 'software engineer',
        'software developer': 'software engineer',
        'programmer': 'software engineer',
        
        'ux designer': 'ux designer',
        'ui designer': 'ux designer',
        'ui/ux designer': 'ux designer',
        'user experience designer': 'ux designer',
        
        'web developer': 'web developer',
        'web dev': 'web developer',
        'website developer': 'web developer',
        
        'frontend developer': 'frontend developer',
        'front-end developer': 'frontend developer',
        'front end developer': 'frontend developer',
        'fe developer': 'frontend developer',
        
        'backend developer': 'backend developer',
        'back-end developer': 'backend developer',
        'back end developer': 'backend developer',
        'be developer': 'backend developer',
        
        'digital marketer': 'digital marketer',
        'digital marketing': 'digital marketer',
        'online marketer': 'digital marketer',
        
        'data analyst': 'data analyst',
        'business intelligence analyst': 'data analyst',
        'bi analyst': 'data analyst',
        
        'product manager': 'product manager',
        'pm': 'product manager',
        'product owner': 'product manager',
        
        'cybersecurity analyst': 'cybersecurity analyst',
        'security analyst': 'cybersecurity analyst',
        'infosec analyst': 'cybersecurity analyst',
        'cyber security analyst': 'cybersecurity analyst',
        
        'devops engineer': 'devops engineer',
        'devops': 'devops engineer',
        'site reliability engineer': 'devops engineer',
        'sre': 'devops engineer',
        
        'machine learning engineer': 'machine learning engineer',
        'ml engineer': 'machine learning engineer',
        'ai engineer': 'machine learning engineer',
        
        'business analyst': 'business analyst',
        'ba': 'business analyst',
        
        'project manager': 'project manager',
        'project management': 'project manager',
        
        'marketing manager': 'marketing manager',
        'marketing lead': 'marketing manager'
    }
    
    # Get the standardized role name if available, otherwise use the original
    standard_role = role_mapping.get(normalized_job_role, normalized_job_role)
    
    # Get the roadmap for the standardized role
    roadmap = roadmaps.get(standard_role, None)
    
    if roadmap:
        # Calculate total weeks
        total_weeks = sum(step['weeks'] for step in roadmap.values())
        return render_template('roadmap.html', job_role=job_role.title(), roadmap=roadmap, total_weeks=total_weeks)
    else:
        return "Roadmap not available for this role. Please check available career paths or contact an advisor."

@app.route('/job_recommendation', methods=['GET', 'POST'])
@login_required
def job_recommendation():
    if request.method == 'POST':
        # Get user inputs
        user_data = [
            int(request.form.get('DSA')),
            int(request.form.get('DBMS')),
            int(request.form.get('OS')),
            int(request.form.get('CN')),
            int(request.form.get('Mathmetics')),
            int(request.form.get('Aptitute')),
            int(request.form.get('Comm')),
            int(request.form.get('Problem_Solving')),
            int(request.form.get('Creative')),
            int(request.form.get('Hackathons'))
        ]

        # Load model and encoder
        with open('job_model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open('label_encoder.pkl', 'rb') as f:
            label_encoder = pickle.load(f)

        # Predict job profile
        # Get top 3 job predictions
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba([user_data])[0]
            top_3_indices = probabilities.argsort()[-3:][::-1]
            top_3_jobs = label_encoder.inverse_transform(top_3_indices).tolist()
        else:
        # Fallback if model doesn't support predict_proba
            predicted_profile = model.predict([user_data])
            top_3_jobs = label_encoder.inverse_transform(top_3_indices).tolist()

        return render_template('job_recommendation.html', job_predictions=top_3_jobs)

    return render_template('job_recommendation.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')




PROMPTS = [
    "Write a story about a world where dreams come true.",
    "Describe a day in the life of a time traveler.",
    "A mysterious door appears in your house. What happens next?",
    "You wake up with a superpower. What is it and how do you use it?"
]

def get_prompt():
    return random.choice(PROMPTS)

def check_grammar(story):
    issues = len(re.findall(r'\b(is|are|was|were)\s+a\b', story, re.IGNORECASE))
    return issues

def assess_creativity(story):
    unique_words = set(story.split())
    return min(10, len(unique_words) // 10)

def assess_coherence(story):
    sentences = re.split(r'[.!?]', story)
    return min(10, len(set(sentences)) // 5)

def assess_engagement(story):
    length = len(story.split())
    sentences = re.split(r'[.!?]', story)
    return min(10, (length + len(set(sentences))) // 20)

def get_feedback(story):
    score = (assess_creativity(story) + assess_coherence(story) + (10 - check_grammar(story)) + assess_engagement(story)) / 4
    return f"Overall Score: {score:.2f}/10", score

@app.route('/creativity_test', methods=['GET', 'POST'])
@login_required
def creativity_test():
    if request.method == 'POST':
        data = request.get_json()
        story = data.get("story", "")
        feedback, score = get_feedback(story)
        
        new_assessment = Assessment(user_id=current_user.id, assessment_type='Creativity Test', score=score)
        db.session.add(new_assessment)
        db.session.commit()
        
        return jsonify({"feedback": feedback, "score": score})
    
    return render_template('creativity_test.html', prompt=get_prompt())

@app.route('/communication_test', methods=['GET', 'POST'])
@login_required
def communication_test():
    if request.method == 'POST':
        data = request.get_json()
        response = data.get("text", "")
        feedback, score = get_feedback(response)
        
        new_assessment = Assessment(user_id=current_user.id, assessment_type='Communication Test', score=score)
        db.session.add(new_assessment)
        db.session.commit()
        
        return jsonify({"feedback": feedback, "score": score})
    
    return render_template('communication_test.html')


@app.route('/careers', methods=['GET', 'POST'])
def careers():
    career_info = None  # Default to None

    if request.method == "POST":
        career_name = request.form.get("career_name")  # Get input safely
        if career_name:
            career_info = scrape_career_details(career_name)  # Fetch details

    return render_template("careers.html", career_info=career_info)

@app.route('/assessment/<type>')
@login_required
def take_assessment(type):
    return render_template(f'assessments/{type}.html')

@app.route('/submit_assessment', methods=['POST'])
@login_required
def submit_assessment():
    assessment_type = request.form.get('type')
    score = float(request.form.get('score'))
    
    new_assessment = Assessment(
        user_id=current_user.id,
        assessment_type=assessment_type,
        score=score
    )
    
    db.session.add(new_assessment)
    db.session.commit()
    
    flash('Assessment submitted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/industry_trends', methods=['GET', 'POST'])
def industry_trends():
    job_info = None
    if request.method == 'POST':
        job_role = request.form.get('job_role')

        trend_data = get_industry_trends(job_role)
        job_info = {
            'role': job_role,
            'description': trend_data.get("description", "No description available."),
            'trend_score': trend_data.get("trend_score"),
            'companies': trend_data.get("companies", []),
            'salary': trend_data.get("salary", "Not available")
        }
    return render_template('industry_trends.html', job_info=job_info)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)