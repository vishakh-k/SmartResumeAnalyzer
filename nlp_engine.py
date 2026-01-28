import re
import os
from collections import Counter

# Try importing pdfminer, fallback to basic text processing if not found
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

class ResumeParser:
    def __init__(self):
        # Master list of skills for keyword matching
        self.skill_database = {
            'Data Science': ['python', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'keras', 'sql', 'matplotlib', 'seaborn', 'nlp', 'machine learning'],
            'Web Development': ['html', 'css', 'javascript', 'react', 'angular', 'vue', 'node.js', 'flask', 'django', 'php', 'laravel'],
            'Java Developer': ['java', 'spring', 'hibernate', 'maven', 'gradle', 'junit', 'jvm'],
            'DevOps': ['docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'linux', 'bash', 'ci/cd']
        }
        
    def extract_text_from_pdf(self, pdf_path):
        text = ""
        if PdfReader:
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    text += page.extract_text()
            except Exception as e:
                print(f"Error reading PDF: {e}")
                return ""
        return text

    def extract_email(self, text):
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else "Not Found"

    def extract_mobile_number(self, text):
        # Basic pattern for mobile numbers
        phone_pattern = r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})'
        match = re.search(phone_pattern, text)
        return match.group(0) if match else "Not Found"
    
    def extract_name(self, text):
        # Simplistic name extraction: First line or Capitalized words at start
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line.split()) < 4: # Assuming name is short
                return line
        return "Candidate"

    def extract_experience(self, text):
        # Look for "X years", "X+ years"
        exp_pattern = r'(\d+(\.\d+)?)\+?\s?years?'
        matches = re.findall(exp_pattern, text.lower())
        if matches:
            # Get the max number found, assuming it mentions total experience somewhere
            try:
                years = [float(m[0]) for m in matches]
                return max(years)
            except:
                return 0
        return 0

    def extract_skills(self, text):
        text_lower = text.lower()
        found_skills = set()
        skill_counts = Counter()

        for category, skills in self.skill_database.items():
            for skill in skills:
                if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                    found_skills.add(skill)
                    skill_counts[category] += 1
        
        return list(found_skills), skill_counts

    def check_sections(self, text_lower):
        sections = {
            'Education': ['education', 'university', 'college', 'degree', 'bachelor', 'master', 'phd'],
            'Experience': ['experience', 'work history', 'employment', 'internship'],
            'Skills': ['skills', 'technical skills', 'competencies', 'technologies'],
            'Projects': ['projects', 'personal projects', 'academic projects']
        }
        found_sections = []
        for section, keywords in sections.items():
            if any(k in text_lower for k in keywords):
                found_sections.append(section)
        return found_sections

    def check_contact_info(self, text, email, mobile):
        score = 0
        missing = []
        if email != "Not Found": score += 10
        else: missing.append("Email")
        
        if mobile != "Not Found": score += 10
        else: missing.append("Mobile Number")
        
        # Check for LinkedIn/Github links
        links = re.findall(r'(linkedin\.com|github\.com)', text.lower())
        if links: score += 5
        
        return score, missing

    def check_action_verbs(self, text_lower):
        # List of strong action verbs
        action_verbs = [
            'developed', 'led', 'managed', 'created', 'designed', 'implemented', 'optimized',
            'improved', 'analyzed', 'collaborated', 'engineered', 'launched', 'spearheaded',
            'mentored', 'orchestrated', 'streamlined', 'automated'
        ]
        found_verbs = [verb for verb in action_verbs if verb in text_lower]
        unique_verbs = len(set(found_verbs))
        
        # 1 point per unique verb, max 20 points
        score = min(20, unique_verbs * 2)
        return score, found_verbs

    def calculate_ats_score(self, skill_count, best_category, found_sections, contact_score, action_verb_score, experience):
        # Weightage:
        # Skills: 40%
        # Sections: 20%
        # Contact Info: 20% (Max 25)
        # Action Verbs: 20%
        # Experience: Bonus 5%
        
        # 1. Skills Score (Max 40)
        # Expect at least 6 relevant skills for full marks
        skills_score = min(40, int((skill_count / 6) * 40))
        
        # 2. Sections Score (Max 20)
        # 5 points per section
        sections_score = len(found_sections) * 5
        
        # 3. Contact Score (Calculated previously, Max 25 usually)
        # We cap it at 20 for this distribution or adjust weights. Let's keep it as passed.
        c_score = min(20, contact_score)
        
        # 4. Action Verbs (Passed directly, Max 20)
        av_score = action_verb_score
        
        total_score = skills_score + sections_score + c_score + av_score
        
        # Bonus for experience
        if experience > 1:
            total_score += 5
            
        return min(100, total_score), {
            "skills_score": skills_score,
            "sections_score": sections_score,
            "contact_score": c_score,
            "action_verb_score": av_score
        }

    def predict_role_and_score(self, skill_counts, found_skills, text_lower, email, mobile, experience):
        if not skill_counts:
            return "Unknown", 0, [], [], {}

        # Predict role based on max skill matches
        best_category = skill_counts.most_common(1)[0][0]
        skill_count = skill_counts[best_category]
        
        # Analysis Steps
        found_sections = self.check_sections(text_lower)
        contact_score, missing_contact = self.check_contact_info(text_lower, email, mobile)
        action_verb_score, found_verbs = self.check_action_verbs(text_lower)
        
        # Calculate Comprehensive ATS Score
        total_score, breakdown = self.calculate_ats_score(
            skill_count, best_category, found_sections, contact_score, action_verb_score, experience
        )

        # Recommendations
        all_category_skills = self.skill_database.get(best_category, [])
        missing_skills = [s for s in all_category_skills if s not in found_skills]
        recommended_skills = missing_skills[:5]

        recommended_courses = []
        if best_category == 'Data Science':
            recommended_courses = ["Coursera: Machine Learning by Andrew Ng", "Udemy: Python for Data Science"]
        elif best_category == 'Web Development':
            recommended_courses = ["FreeCodeCamp: Full Stack Certification", "Udemy: The Web Developer Bootcamp"]
            
        # Add feedback to breakdown
        breakdown['missing_sections'] = [s for s in ['Education', 'Experience', 'Skills', 'Projects'] if s not in found_sections]
        breakdown['missing_contact'] = missing_contact
        breakdown['action_verbs_count'] = len(found_verbs)
        
        return best_category, total_score, recommended_skills, recommended_courses, breakdown

    def parse(self, pdf_path):
        text = self.extract_text_from_pdf(pdf_path)
        
        email = self.extract_email(text)
        mobile = self.extract_mobile_number(text)
        name = self.extract_name(text)
        experience = self.extract_experience(text)
        
        skills, skill_counts = self.extract_skills(text)
        
        role, score, rec_skills, courses, breakdown = self.predict_role_and_score(
            skill_counts, skills, text.lower(), email, mobile, experience
        )
        
        return {
            "name": name,
            "email": email,
            "mobile_number": mobile,
            "skills": skills,
            "total_experience": experience,
            "predicted_role": role,
            "resume_score": score,
            "recommended_skills": rec_skills,
            "recommended_courses": courses,
            "score_breakdown": breakdown,
            "text": text
        }
