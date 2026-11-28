''' EXAMPLE USEAGE
if __name__ == "__main__":
    retriever = CareerAssistantRetriever()
    
    # Simulate a student query from the backend
    results = retriever.search_companies(
        student_major="Computer Science",
        target_region="colorado",
        limit=5
    )
    
    print(f"Found {len(results)} matching companies:")
    for company in results:
        print(f"- {company.get('company_name')} ({company.get('location')}) -> Website: {company.get('website')}")
'''


import json
import os

class CareerAssistantRetriever:
    def __init__(self, base_dir="partitioned_data"):
        self.base_dir = base_dir
        self.manifest_path = os.path.join(base_dir, "manifest.json")
        self.manifest = self._load_manifest()

    def _load_manifest(self):
        if not os.path.exists(self.manifest_path):
            raise FileNotFoundError(f"Manifest not found at {self.manifest_path}. Run your partitioning script first.")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def search_companies(self, student_major=None, target_region=None, target_industry=None, limit=10):
        """
        Retrieves matching companies based on student criteria by routing 
        directly to the appropriate partitioned JSON files.
        """
        candidate_companies = []
        loaded_files = set()

        # Route via Major partition if provided
        if student_major:
            major_filename = f"{student_major.lower().replace(' ', '_')}.json"
            file_path = os.path.join(self.base_dir, "by_major", major_filename)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    candidate_companies.extend(json.load(f))
                    loaded_files.add(major_filename)

        # Route via Industry partition if provided
        if target_industry:
            ind_filename = f"{target_industry.lower().replace(' ', '_')}.json"
            file_path = os.path.join(self.base_dir, "by_industry", ind_filename)
            if os.path.exists(file_path) and ind_filename not in loaded_files:
                with open(file_path, "r", encoding="utf-8") as f:
                    candidate_companies.extend(json.load(f))
                    loaded_files.add(ind_filename)

        # If no specific major or industry matched or was provided, fall back to region or load a default subset
        if not candidate_companies and target_region:
            reg_filename = f"{target_region}.json"
            file_path = os.path.join(self.base_dir, "by_region", reg_filename)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    candidate_companies.extend(json.load(f))

        # Deduplicate companies by name
        seen_names = set()
        unique_companies = []
        for comp in candidate_companies:
            name = comp.get("company_name")
            if name and name not in seen_names:
                seen_names.add(name)
                # Apply secondary post-filtering if multiple criteria were passed
                if target_region and target_region.lower() not in comp.get("location", "").lower():
                    continue
                unique_companies.append(comp)

        return unique_companies[:limit]