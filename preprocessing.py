import json
import os
import re
from collections import defaultdict

def sanitize_filename(name):
    """Converts strings like 'Energy - Oil & Gas' into clean filenames like 'energy_oil_gas'."""
    clean = re.sub(r'[^a-zA-Z0-9\s-]', '', str(name).lower())
    return re.sub(r'[\s-]+', '_', clean).strip('_') or "unknown"

# Keyword mapping to infer college majors directly from your PDF's industry labels
INDUSTRY_TO_MAJORS = {
    "high tech": ["Computer Science", "Software Engineering", "Data Science", "Cybersecurity"],
    "information technology": ["Computer Science", "Information Systems", "Data Science"],
    "civil engineering": ["Civil Engineering", "Structural Engineering", "Environmental Engineering"],
    "construction engineering": ["Civil Engineering", "Construction Management", "Mechanical Engineering"],
    "geotechnical": ["Geological Engineering", "Civil Engineering", "Earth Sciences"],
    "mining": ["Mining Engineering", "Geological Engineering", "Metallurgical Engineering"],
    "metals": ["Metallurgical & Materials Engineering", "Mechanical Engineering", "Chemical Engineering"],
    "oil & gas": ["Petroleum Engineering", "Chemical Engineering", "Mechanical Engineering"],
    "alternative/renewable": ["Electrical Engineering", "Mechanical Engineering", "Environmental Engineering"],
    "utilities/power": ["Electrical Engineering", "Mechanical Engineering", "Energy Systems"],
    "aerospace": ["Aerospace Engineering", "Mechanical Engineering", "Electrical Engineering"],
    "manufacturing": ["Mechanical Engineering", "Industrial Engineering", "Manufacturing Engineering"],
    "electronics": ["Electrical Engineering", "Computer Engineering", "Physics"],
    "biotech": ["Bioengineering", "Chemical Engineering", "Biology", "Chemistry"],
    "healthcare": ["Bioengineering", "Biomedical Engineering", "Health Sciences"],
    "environmental": ["Environmental Engineering", "Environmental Science", "Chemistry"],
    "chemicals": ["Chemical Engineering", "Chemistry", "Materials Science"],
    "banking": ["Finance", "Economics", "Applied Mathematics", "Data Science"],
    "education": ["Education", "STEM Education", "Administration"],
    "government": ["Public Policy", "Civil Engineering", "Environmental Science"],
}

def infer_majors(industry_str):
    """Maps an industry string to matching college majors."""
    ind_lower = industry_str.lower()
    matched_majors = set()
    for keyword, majors in INDUSTRY_TO_MAJORS.items():
        if keyword in ind_lower:
            matched_majors.update(majors)
    return sorted(list(matched_majors)) if matched_majors else ["General Engineering & Business"]

def get_company_scale(type_size_str):
    """Categorizes company size strings into Small/Startup, Mid-Market, or Enterprise."""
    text = type_size_str.lower()
    if any(k in text for k in ["1-10", "11-50"]):
        return "small_startup_1_to_50"
    elif any(k in text for k in ["51-200", "201-500", "501-1000"]):
        return "mid_market_51_to_1000"
    elif any(k in text for k in ["1001-5000", "5001-10,000", "10,001+"]):
        return "enterprise_1000_plus"
    return "unspecified_scale"

def get_region(location_str):
    """Groups companies into regional hubs based on your dataset's locations."""
    loc = location_str.lower()
    if "colorado" in loc or any(city in loc for city in ["denver", "golden", "boulder", "lakewood", "littleton", "englewood", "broomfield"]):
        return "colorado_hub"
    elif any(state in loc for state in ["texas", "oklahoma", "new mexico", "arizona"]):
        return "southwest_hub"
    elif any(state in loc for state in ["california", "washington", "oregon", "nevada", "utah"]):
        return "west_coast_mountain_hub"
    elif "united states" in loc:
        return "other_us_states"
    elif loc != "unknown" and loc.strip() != "":
        return "international"
    return "location_unspecified"

def partition_company_data(input_json_path, base_output_dir="partitioned_data"):
    with open(input_json_path, "r", encoding="utf-8") as f:
        companies = json.load(f)

    # Create organized folders
    dirs = {
        "industry": os.path.join(base_output_dir, "by_industry"),
        "major": os.path.join(base_output_dir, "by_major"),
        "region": os.path.join(base_output_dir, "by_region"),
        "scale": os.path.join(base_output_dir, "by_scale"),
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    buckets = {
        "industry": defaultdict(list),
        "major": defaultdict(list),
        "region": defaultdict(list),
        "scale": defaultdict(list),
    }

    for company in companies:
        # 1. Enrich with inferred majors if not already present
        industry = company.get("industry", "Unknown")
        if "matching_majors" not in company or not company["matching_majors"]:
            company["matching_majors"] = infer_majors(industry)

        # 2. Group by Industry
        ind_key = sanitize_filename(industry)
        buckets["industry"][ind_key].append(company)

        # 3. Group by Major (a company can appear in multiple major files)
        for major in company["matching_majors"]:
            maj_key = sanitize_filename(major)
            buckets["major"][maj_key].append(company)

        # 4. Group by Region
        reg_key = get_region(company.get("location", "Unknown"))
        buckets["region"][reg_key].append(company)

        # 5. Group by Scale
        scale_key = get_company_scale(company.get("company_type_size", "Unknown"))
        buckets["scale"][scale_key].append(company)

    # Save partitioned files and build a routing manifest
    manifest = {"total_companies": len(companies), "partitions": {}}

    for category, group_dict in buckets.items():
        manifest["partitions"][category] = {}
        for key, items in group_dict.items():
            # Optional: Sub-chunk if a file exceeds 250 companies to keep LLM token usage low
            chunk_size = 250
            if len(items) > chunk_size:
                for idx in range(0, len(items), chunk_size):
                    chunk = items[idx : idx + chunk_size]
                    part_num = (idx // chunk_size) + 1
                    filename = f"{key}_part{part_num}.json"
                    filepath = os.path.join(dirs[category], filename)
                    with open(filepath, "w", encoding="utf-8") as out:
                        json.dump(chunk, out, indent=2, ensure_ascii=False)
                    manifest["partitions"][category][filename] = len(chunk)
            else:
                filename = f"{key}.json"
                filepath = os.path.join(dirs[category], filename)
                with open(filepath, "w", encoding="utf-8") as out:
                    json.dump(items, out, indent=2, ensure_ascii=False)
                manifest["partitions"][category][filename] = len(items)

    # Save manifest index for your LLM router
    manifest_path = os.path.join(base_output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as m_out:
        json.dump(manifest, m_out, indent=2)

    print(f"Partitioning complete! Files saved in './{base_output_dir}/'")
    print(f"Routing manifest saved to '{manifest_path}'")

if __name__ == "__main__":
    partition_company_data("companies_with_websites.json")