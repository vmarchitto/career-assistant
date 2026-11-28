import re
import json
import pdfplumber

def parse_resume(pdf_path):
    extracted_text = ""
    
    # 1. Extract raw text from the PDF
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
                
    # 2. Define the schema structure
    resume_data = {
        "raw_text": extracted_text.strip(),
        "contact_info": {
            "email": extract_email(extracted_text),
            "phone": extract_phone(extracted_text),
            "linkedin": extract_linkedin(extracted_text)
        },
        "skills": extract_skills(extracted_text),
        "education": extract_education(extracted_text),
        "inferred_major": detect_major(extracted_text)
    }
    
    return resume_data

def extract_email(text):
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return email_match.group(0) if email_match else None

def extract_phone(text):
    phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    return phone_match.group(0) if phone_match else None

def extract_linkedin(text):
    linkedin_match = re.search(r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+", text)
    return linkedin_match.group(0) if linkedin_match else None

def extract_skills(text):
    """
    Scans for a common 'Skills' header and extracts subsequent technical keywords.
    """
    common_skills = [
        "Python", "Java", "C++", "JavaScript", "SQL", "React", "Docker", 
        "Git", "Machine Learning", "Data Analysis", "AutoCAD", "SolidWorks",
        "Matlab", "Project Management", "Agile", "Linux", "AWS", "TensorFlow"
    ]
    found_skills = [skill for skill in common_skills if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE)]
    return found_skills

def extract_education(text):
    """
    Simple pattern search for university degrees.
    """
    degrees = ["Bachelor", "Master", "Ph.D.", "B.S.", "M.S.", "B.A.", "B.E."]
    found_degrees = []
    for line in text.split('\n'):
        if any(deg in line for deg in degrees):
            found_degrees.append(line.strip())
    return found_degrees

def detect_major(text):
    """
    Infers the student's major based on common keywords in their resume text.
    """
    text_lower = text.lower()
    if "computer science" in text_lower or "software" in text_lower:
        return "Computer Science"
    elif "civil engineering" in text_lower:
        return "Civil Engineering"
    elif "mechanical engineering" in text_lower:
        return "Mechanical Engineering"
    elif "petroleum" in text_lower:
        return "Petroleum Engineering"
    elif "mining" in text_lower:
        return "Mining Engineering"
    elif "electrical" in text_lower:
        return "Electrical Engineering"
    elif "finance" in text_lower or "economics" in text_lower:
        return "Finance"
    return "General Engineering"

if __name__ == "__main__":
    # Test the parser with a sample resume PDF
    pdf_file = "sample_student_resume.pdf"
    
    try:
        parsed_data = parse_resume(pdf_file)
        print(json.dumps(parsed_data, indent=4))
    except FileNotFoundError:
        print(f"Could not find {pdf_file}. Please place a sample resume in the directory to test.")