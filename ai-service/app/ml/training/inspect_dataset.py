import json
from pathlib import Path

# Locate the dataset
DATASET_PATH = Path("data/raw/train.json")

# Load JSON
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    dataset = json.load(f)

print(f"Loaded {len(dataset)} resumes.")

# Extract the first sample
sample = dataset[0]

print("\nResume Preview")
print("-" * 40)
print(sample["text"][:300])

print("\nAnnotations")
print("-" * 40)
for start, end, label in sample["annotations"]:
    entity = sample["text"][start:end]
    print(f"{label:<15} -> {entity}")
