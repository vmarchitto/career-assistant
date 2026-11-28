import re
import json
import pdfplumber

def parse_company_pdf(pdf_path, output_json_path):
    companies = []
    
    print(f"Opening PDF: {pdf_path}...")
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
                
            # Split text into non-empty lines
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Skip page footer artifacts (e.g., "Page 1", "Page 2")
                if re.match(r"^Page\s+\d+$", line, re.IGNORECASE):
                    i += 1
                    continue
                
                company_entry = {
                    "company_name": line,
                    "industry": "Unknown",
                    "location": "Unknown",
                    "company_type_size": "Unknown"
                }
                
                # Look ahead for Industry / Sector and Location line (e.g., "Construction Engineering - United States")
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # Check if the next line looks like an industry/location line
                    if " - " in next_line or any(loc in next_line for loc in ["United States", "Colorado", "Canada", "District of Columbia"]):
                        parts = next_line.split(" - ", 1)
                        company_entry["industry"] = parts[0].strip()
                        if len(parts) > 2:
                            company_entry["location"] = parts[1].strip()
                        i += 1
                
                # Look ahead for Company Size / Type (e.g., "Private company with 501-1000 employees")
                if i + 1 < len(lines):
                    sub_next = lines[i + 1]
                    lower_sub = sub_next.lower()
                    if any(kw in lower_sub for kw in ["private company", "public company", "non-profit", "government", "employees", "organization"]):
                        company_entry["company_type_size"] = sub_next.strip()
                        i += 1
                
                companies.append(company_entry)
                i += 1
                
            print(f"Processed page {page_num}/{len(pdf.pages)}")

    # Save extracted records to JSON
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(companies, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully extracted {len(companies)} company entries to {output_json_path}")

if __name__ == "__main__":
    PDF_FILE = "LLMProject_CompanyNames3.pdf"
    OUTPUT_JSON = "extracted_companies.json"
    
    parse_company_pdf(PDF_FILE, OUTPUT_JSON)