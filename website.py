import json
from ddgs import DDGS

def find_company_websites(input_json_path, output_json_path):
    # Load your existing company data
    with open(input_json_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)
    
    updated_companies = []
    print(f"Starting web search for {len(companies)} companies...")
    
    # Initialize the DuckDuckGo search client
    with DDGS() as ddgs:
        for idx, company in enumerate(companies):
            name = company.get("company_name", "")
            location = company.get("location", "Unknown")
            
            # Formulate a clean search query
            query = f"{name} {location} official website"
            
            try:
                # Retrieve the top search result link
                results = list(ddgs.text(query, max_results=1))
                if results:
                    company["website"] = results[0].get("href")
                else:
                    company["website"] = None
            except Exception as e:
                print(f"Error searching for {name}: {e}")
                company["website"] = None
                
            updated_companies.append(company)
            
            # Print progress every 25 companies
            if (idx + 1) % 25 == 0:
                print(f"Processed {idx + 1}/{len(companies)} companies...")

    # Save the updated dataset
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(updated_companies, f, indent=4, ensure_ascii=False)
        
    print(f"Done! Results saved to {output_json_path}")

if __name__ == "__main__":
    # Replace with your actual file names
    find_company_websites("extracted_companies.json", "companies_with_websites.json")