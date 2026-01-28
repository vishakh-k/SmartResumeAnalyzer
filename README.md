# Smart Resume Analyzer

Smart Resume Analyzer is an AI-powered tool designed to help job seekers optimize their resumes. It parses resumes, analyzes skills, predicts suitable job roles, and provides actionable feedback to improve ATS (Applicant Tracking System) compatibility.

## Features

- **Smart Parsing**: Automatically extracts details like name, email, mobile number, and skills from PDF resumes.
- **Job Prediction**: Predicts the most suitable job role (e.g., Data Science, Web Development) based on skills and experience.
- **Resume Scoring**: Gives a compatibility score (0-100) based on skills, action verbs, and contact information.
- **Detailed Feedback**: Provides a breakdown of missing sections, skills, and improvement areas.
- **Course Recommendations**: Suggests relevant courses to bridge skill gaps.
- **User Dashboard**: Users can upload resumes, view history, and track improvements.
- **Admin Dashboard**: Analytics on user demographics, role distribution, and system usage.
- **Secure Authentication**: User registration and login protected with Bcrypt hashing.

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (Development) / MySQL (Production ready)
- **Frontend**: HTML5, CSS3, JavaScript
- **NLP & Analysis**: PyPDF2, Regex, Custom Skill Matching
- **Visualization**: Chart.js

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/vishakh-k/SmartResumeAnalyzer.git
    cd SmartResumeAnalyzer
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application**:
    ```bash
    python app.py
    ```

5.  Open your browser and navigate to `http://127.0.0.1:5000`.

## Usage

1.  **Register/Login**: Create a new account to access the dashboard.
2.  **Upload Resume**: Upload your resume in PDF format.
3.  **View Results**: Get instant analysis, scores, and recommendations.
4.  **Admin Panel**: Login with separate admin credentials (if configured) or view `admin_dashboard` logic in `app.py`.

## Project Structure

- `app.py`: Main Flask application entry point.
- `nlp_engine.py`: Logic for parsing PDFs and analyzing content.
- `templates/`: HTML files for various pages.
- `static/`: CSS styles and file uploads.
- `instance/`: Database storage (SQLite).

## License

This project is open-source and available under the [MIT License](LICENSE).
