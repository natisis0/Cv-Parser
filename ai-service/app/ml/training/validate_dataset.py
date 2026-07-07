import json
from pathlib import Path

# Locate the dataset
DATASET_PATH = Path("data/raw/train.json")

# Load JSON
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    dataset = json.load(f)

print(f"Loaded {len(dataset)} resumes.")

error_count = 0
bad_resumes = set()

# Loop through every sample and validation check
for resume_index, sample in enumerate(dataset):
    text = sample.get("text", "")
    annotations = sample.get("annotations", [])
    
    for start, end, label in annotations:
        # Check if indices are valid
        if start >= end:
            print(f"Resume {resume_index}: Invalid entity positions ({start}, {end})")
            error_count += 1
            bad_resumes.add(resume_index)
            continue
            
        # Check if the annotation goes past the text length
        if end > len(text):
            print(f"Resume {resume_index}: Entity exceeds text length")
            error_count += 1
            bad_resumes.add(resume_index)
            continue
            
        # Extract entity
        entity = text[start:end]
        
        # Check if it's empty or whitespace only
        if entity.strip() == "":
            print(f"Resume {resume_index}: Empty entity")
            error_count += 1
            bad_resumes.add(resume_index)

print()
if error_count == 0:
    print("Dataset validation passed!")
else:
    print(f"Found {error_count} errors.")
    print(f"Resumes with errors: {len(bad_resumes)}")
