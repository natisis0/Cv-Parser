"""
Two-stage Gemini-powered dataset labeling pipeline.

Stage 1: Extract text from resumes → send to Gemini → get entity annotations (label + exact text).
Stage 2: Verify entities exist in source text → compute character offsets → save as spaCy-compatible JSON.

Usage:
    python -m scripts.label_dataset --input-dir data/resumes --output data/raw/gemini_dataset.json
    python -m scripts.label_dataset --input-dir data/resumes --output data/raw/gemini_dataset.json --limit 5 --model gemini-2.5-pro
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Add the project root to sys.path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.extractors.factory import get_extractor


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROMPT_PATH = Path(__file__).resolve().parent / "prompt.txt"
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text(file_path: Path) -> str:
    """Extracts text from a resume file using the existing extractor factory."""
    extractor = get_extractor(str(file_path))
    return extractor.extract(str(file_path))


# ---------------------------------------------------------------------------
# Gemini annotation
# ---------------------------------------------------------------------------

def load_prompt_template() -> str:
    """Loads the annotator prompt template from prompt.txt."""
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def annotate_with_gemini(text: str, client: genai.Client, model_name: str) -> list[dict]:
    """
    Sends resume text to Gemini and returns a list of entity dicts.
    Each dict has {"label": "...", "text": "..."}.
    """
    prompt_template = load_prompt_template()
    prompt = prompt_template.replace("{{RESUME_TEXT}}", text)

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    # Extract the response text
    raw_response = response.text.strip()

    # Strip markdown code fences if Gemini wraps the response
    if raw_response.startswith("```"):
        raw_response = re.sub(r"^```(?:json)?\s*", "", raw_response)
        raw_response = re.sub(r"\s*```$", "", raw_response)

    # Parse JSON
    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError as e:
        print(f"    ⚠ Failed to parse Gemini response as JSON: {e}")
        print(f"    Raw response (first 500 chars): {raw_response[:500]}")
        return []

    entities = result.get("entities", [])
    return entities


# ---------------------------------------------------------------------------
# Verification & multi-stage offset computation
# ---------------------------------------------------------------------------

def clean_alphanumeric(text: str) -> str:
    """Helper to convert string to lower-case alphanumeric characters."""
    return "".join(c.lower() for c in text if c.isalnum())


def find_all_occurrences(text: str, entity_text: str) -> list[tuple[int, int]]:
    """
    Finds all start and end offsets of entity_text within text.
    Uses multiple matching strategies:
      1. Exact match (case-sensitive)
      2. Case-insensitive exact match
      3. Whitespace-normalized and punctuation-insensitive match (fuzzy character map)
    
    Returns a list of (start_idx, end_idx) tuples.
    """
    occurrences = []
    
    # Strategy 1: Exact case-sensitive match
    search_start = 0
    while True:
        idx = text.find(entity_text, search_start)
        if idx == -1:
            break
        occurrences.append((idx, idx + len(entity_text)))
        search_start = idx + 1
        
    if occurrences:
        return occurrences

    # Strategy 2: Case-insensitive match
    text_lower = text.lower()
    entity_lower = entity_text.lower()
    search_start = 0
    while True:
        idx = text_lower.find(entity_lower, search_start)
        if idx == -1:
            break
        occurrences.append((idx, idx + len(entity_text)))
        search_start = idx + 1

    if occurrences:
        return occurrences

    # Strategy 3: Whitespace-normalized and punctuation-insensitive match
    # Maps match indices in cleaned text back to original indices.
    cleaned_indices = []
    cleaned_chars = []
    
    for idx, char in enumerate(text):
        if char.isalnum():
            cleaned_chars.append(char.lower())
            cleaned_indices.append(idx)
        elif char.isspace() and (not cleaned_chars or cleaned_chars[-1] != ' '):
            cleaned_chars.append(' ')
            cleaned_indices.append(idx)
            
    cleaned_text = "".join(cleaned_chars)
    
    entity_cleaned = "".join(c.lower() for c in entity_text if c.isalnum() or c.isspace())
    entity_cleaned = " ".join(entity_cleaned.split())  # normalize whitespace
    
    if not entity_cleaned:
        return []
        
    search_start = 0
    while True:
        match_idx = cleaned_text.find(entity_cleaned, search_start)
        if match_idx == -1:
            break
            
        start_orig = cleaned_indices[match_idx]
        end_orig = cleaned_indices[match_idx + len(entity_cleaned) - 1] + 1
        
        occurrences.append((start_orig, end_orig))
        search_start = match_idx + 1
        
    return occurrences


def validate_annotation(text: str, start: int, end: int, original_entity_text: str) -> bool:
    """
    Validates that the annotated text matches the expected text structurally 
    (after stripping out spaces and punctuation).
    """
    sliced_text = text[start:end]
    return clean_alphanumeric(sliced_text) == clean_alphanumeric(original_entity_text)


def verify_and_compute_offsets(
    text: str,
    entities: list[dict],
) -> tuple[list[list], list[dict]]:
    """
    For each entity returned by Gemini:
      1. Verify the text exists in the resume (using advanced matching fallbacks).
      2. Find ALL occurrences and compute [start, end, label] for each.
      3. Assert/validate character offsets contain the correct text.

    Returns:
        (valid_annotations, unmatched_entities)

    valid_annotations: list of [start, end, label]
    unmatched_entities: list of entity dicts that were not found in the text
    """
    valid_annotations: list[list] = []
    unmatched_entities: list[dict] = []

    for entity in entities:
        label = entity.get("label", "").upper().strip()
        entity_text = entity.get("text", "").strip()

        if not label or not entity_text:
            unmatched_entities.append(entity)
            continue

        occurrences = find_all_occurrences(text, entity_text)

        if not occurrences:
            unmatched_entities.append(entity)
            continue

        for start, end in occurrences:
            # Final validation check
            if validate_annotation(text, start, end, entity_text):
                valid_annotations.append([start, end, label])
            else:
                unmatched_entities.append(entity)

    return valid_annotations, unmatched_entities


# ---------------------------------------------------------------------------
# Overlap & duplicate resolution
# ---------------------------------------------------------------------------

def resolve_overlaps_and_duplicates(annotations: list[list]) -> tuple[list[list], int, int]:
    """
    Removes exact duplicate annotations (same start, end, label)
    and overlapping annotations (retaining the longer spans).
    
    Returns:
        (filtered_annotations, duplicate_count, overlap_count)
    """
    # 1. Remove exact duplicates
    seen = set()
    deduplicated = []
    duplicate_count = 0
    
    for ann in annotations:
        start, end, label = ann
        key = (start, end, label)
        if key not in seen:
            seen.add(key)
            deduplicated.append(ann)
        else:
            duplicate_count += 1
            
    # 2. Resolve overlapping spans (similar to spaCy's filter_spans)
    # Sort by start position ascending, then by span length descending (longer spans first)
    sorted_anns = sorted(deduplicated, key=lambda x: (x[0], -(x[1] - x[0])))
    filtered = []
    overlap_count = 0
    
    for ann in sorted_anns:
        start, end, label = ann
        has_overlap = False
        for f_start, f_end, f_label in filtered:
            # Overlap condition: start < f_end and end > f_start
            if start < f_end and end > f_start:
                has_overlap = True
                break
        if not has_overlap:
            filtered.append(ann)
        else:
            overlap_count += 1
            
    # Re-sort by start position ascending
    filtered.sort(key=lambda x: x[0])
    return filtered, duplicate_count, overlap_count



# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load .env file first so env vars are available for argument defaults
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generate NER training data from resumes using Gemini.",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/resumes",
        help="Directory containing resume files (PDF/DOCX).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/gemini_dataset.json",
        help="Output JSON file path.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        help="Gemini model to use (default: GEMINI_MODEL env var or gemini-2.5-flash).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between API calls (default: 1.0).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max number of resumes to process (0 = all).",
    )

    args = parser.parse_args()

    # Define output path
    output_path = Path(args.output)

    # Validate API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.")
        print("Add it to your .env file: GEMINI_API_KEY=your-key-here")
        sys.exit(1)

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)

    # Collect all resume files
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        sys.exit(1)

    resume_files = sorted([
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ])

    if not resume_files:
        print(f"No PDF/DOCX files found in {input_dir}")
        sys.exit(1)

    # Load existing dataset if it exists
    dataset = []
    processed_filenames = set()
    processed_texts = set()

    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                dataset = json.load(f)
                for sample in dataset:
                    if "filename" in sample:
                        processed_filenames.add(sample["filename"])
                    if "text" in sample:
                        processed_texts.add(sample["text"])
            print(f"Loaded existing dataset with {len(dataset)} labeled resumes.")
        except Exception as e:
            print(f"⚠ Warning: Could not parse existing dataset {output_path}: {e}")

    # Filter out files that are already labeled in the dataset
    unprocessed_files = []
    for f in resume_files:
        if f.name in processed_filenames:
            continue
        
        # Check by text content as fallback (e.g. if labeled in a previous version without filename field)
        try:
            text = extract_text(f)
            if text in processed_texts:
                # Associate filename with the existing entry
                for sample in dataset:
                    if sample.get("text") == text:
                        sample["filename"] = f.name
                        processed_filenames.add(f.name)
                        break
                continue
        except Exception:
            pass
            
        unprocessed_files.append(f)

    if args.limit > 0:
        files_to_process = unprocessed_files[:args.limit]
    else:
        files_to_process = unprocessed_files

    print(f"Found {len(resume_files)} resume(s) in input directory.")
    print(f"  - Already Labeled: {len(resume_files) - len(unprocessed_files)}")
    print(f"  - Pending:         {len(unprocessed_files)}")
    if args.limit > 0:
        print(f"  - Limit:           Will process up to {args.limit} pending resume(s) this run.")
    print(f"Model: {args.model}")
    print(f"Output Dataset: {args.output}")
    print()

    # Process new resumes
    total_errors = 0
    new_labeled_count = 0
    
    total_gemini_entities = 0
    total_unmatched_entities = 0
    total_duplicate_annotations = 0
    total_overlapping_annotations = 0
    total_valid_annotations = 0
    
    for i, file_path in enumerate(files_to_process, start=1):
        filename = file_path.name
        print(f"[{i}/{len(files_to_process)}] Querying Gemini for new resume: {filename}...")
        
        # 1. Extract text
        try:
            text = extract_text(file_path)
        except Exception as e:
            print(f"    ✘ Extraction error: {e}")
            total_errors += 1
            continue

        if not text.strip():
            print("    ✘ Error: Empty text after extraction")
            total_errors += 1
            continue

        # 2. Call Gemini (with automatic retry for 429 rate limits)
        max_retries = 5
        retry_delay = 30
        success = False
        
        for attempt in range(1, max_retries + 1):
            try:
                entities = annotate_with_gemini(text, client, args.model)
                success = True
                break
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                    print(f"    ⚠ Rate limit hit (429) on attempt {attempt}/{max_retries}. Pausing for {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"    ✘ Gemini API error: {e}")
                    break
        
        if not success:
            total_errors += 1
            continue

        total_gemini_entities += len(entities)

        # 3. Match & Verify offsets
        valid_anns, unmatched = verify_and_compute_offsets(text, entities)
        total_unmatched_entities += len(unmatched)

        # 4. Resolve duplicates & overlaps
        filtered_anns, dup_count, overlap_count = resolve_overlaps_and_duplicates(valid_anns)
        
        total_duplicate_annotations += dup_count
        total_overlapping_annotations += overlap_count
        total_valid_annotations += len(filtered_anns)

        if unmatched:
            print(f"    ⚠ {len(unmatched)} unmatched entities:")
            for ue in unmatched[:3]:
                print(f"      - [{ue.get('label')}] \"{ue.get('text', '')[:50]}\"")

        print(
            f"    ✔ Entities: {len(entities)} | "
            f"Unmatched: {len(unmatched)} | "
            f"Annotations: {len(filtered_anns)} "
            f"(Duplicates removed: {dup_count}, Overlaps removed: {overlap_count})"
        )

        sample = {
            "filename": filename,
            "text": text,
            "annotations": filtered_anns,
        }
        dataset.append(sample)
        new_labeled_count += 1

        # Save immediately after each file to prevent data loss
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        # Rate limiting delay
        if i < len(files_to_process) and args.delay > 0:
            time.sleep(args.delay)

    # Compute final metrics & entity stats across the entire compiled dataset
    compilation_count = len(dataset)
    total_compilation_annotations = 0
    entity_stats = {}

    for sample in dataset:
        anns = sample.get("annotations", [])
        total_compilation_annotations += len(anns)
        for ann in anns:
            label = ann[2]
            entity_stats[label] = entity_stats.get(label, 0) + 1

    # Print summary report
    print()
    print("=" * 60)
    print(" LABELING PIPELINE REPORT")
    print("=" * 60)
    print(f"Resumes in input directory:    {len(resume_files)}")
    print(f"Total Labeled in Dataset:      {compilation_count}")
    print(f"Newly Labeled this run:        {new_labeled_count}")
    print(f"Errors this run:               {total_errors}")
    print("-" * 60)
    if new_labeled_count > 0:
        match_rate = (1.0 - (total_unmatched_entities / total_gemini_entities)) * 100 if total_gemini_entities > 0 else 0
        print(f"New Run Match Rate:            {match_rate:.1f}%")
    print(f"Total Annotations in Dataset:  {total_compilation_annotations}")
    if compilation_count > 0:
        print(f"Average Annotations/Resume:    {total_compilation_annotations / compilation_count:.1f}")
    print("-" * 60)
    print("Entity Statistics (Entire Dataset):")
    for label in sorted(entity_stats.keys()):
        print(f"  {label:<20} {entity_stats[label]}")
    print("-" * 60)
    print(f"Output Dataset:                {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
