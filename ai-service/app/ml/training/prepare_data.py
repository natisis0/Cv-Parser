import json
import random
from pathlib import Path
import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans

def load_dataset(path: Path) -> list:
    """Loads dataset from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def split_dataset(
    dataset: list, 
    train_ratio: float = 0.8, 
    dev_ratio: float = 0.1, 
    test_ratio: float = 0.1, 
    seed: int = 42
) -> tuple[list, list, list]:
    """Shuffles the dataset deterministically and splits it into train, dev, and test sets."""
    dataset_copy = list(dataset)
    random.seed(seed)
    random.shuffle(dataset_copy)
    
    total = len(dataset_copy)
    train_end = int(total * train_ratio)
    dev_end = int(total * (train_ratio + dev_ratio))
    
    train = dataset_copy[:train_end]
    dev = dataset_copy[train_end:dev_end]
    test = dataset_copy[dev_end:]
    
    return train, dev, test

def deduplicate_dataset(dataset: list) -> list:
    """Removes duplicate samples from the dataset based on text content."""
    seen_texts = set()
    deduplicated = []
    for sample in dataset:
        text = sample.get("text", "")
        if text not in seen_texts:
            seen_texts.add(text)
            deduplicated.append(sample)
    return deduplicated

def convert_to_docbin(dataset: list, nlp: spacy.language.Language) -> tuple[DocBin, dict]:
    """Converts the dataset to a DocBin and tracks statistics."""
    doc_bin = DocBin()
    stats = {
        "processed_docs": 0,
        "total_annotations": 0,
        "valid_spans": 0,
        "skipped_invalid_spans": 0,
        "filtered_overlapping_spans": 0,
    }
    
    for sample in dataset:
        text = sample.get("text", "")
        annotations = sample.get("annotations", [])
        
        # Clean surrogates to prevent Cython UTF-8 encode crashes
        text = "".join(" " if 0xD800 <= ord(c) <= 0xDFFF else c for c in text)
        
        doc = nlp.make_doc(text)
        spans = []
        
        stats["processed_docs"] += 1
        stats["total_annotations"] += len(annotations)
        
        for start, end, label in annotations:
            # Clip start and end to text boundaries
            start = max(0, start)
            end = min(len(text), end)
            
            # Trim leading/trailing whitespace to prevent SpaCy whitespace errors
            while start < end and text[start].isspace():
                start += 1
            while start < end and text[end - 1].isspace():
                end -= 1
                
            # Skip invalid spans: index bounds error or empty span
            if start >= end or text[start:end].strip() == "":
                stats["skipped_invalid_spans"] += 1
                continue
                
            span = doc.char_span(start, end, label=label)
            if span is None:
                stats["skipped_invalid_spans"] += 1
                continue
            
            spans.append(span)
            
        # Filter overlapping / duplicate spans using SpaCy's utility
        filtered_spans = filter_spans(spans)
        stats["filtered_overlapping_spans"] += (len(spans) - len(filtered_spans))
        stats["valid_spans"] += len(filtered_spans)
        
        doc.ents = filtered_spans
        doc_bin.add(doc)
        
    return doc_bin, stats

def save_docbin(doc_bin: DocBin, path: Path) -> None:
    """Saves the DocBin to the specified path, creating directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc_bin.to_disk(path)

def main():
    # Define paths
    raw_data_path = Path("data/raw/train.json")
    processed_dir = Path("data/processed")
    
    train_path = processed_dir / "train.spacy"
    dev_path = processed_dir / "dev.spacy"
    test_path = processed_dir / "test.spacy"
    report_path = processed_dir / "report.json"
    
    # Initialize blank English SpaCy model
    nlp = spacy.blank("en")
    
    # 1. Load Dataset
    print(f"Loading raw dataset from {raw_data_path}...")
    dataset = load_dataset(raw_data_path)
    total_docs = len(dataset)
    print(f"Loaded {total_docs} resumes.")
    
    # Deduplicate dataset based on text content
    print("Deduplicating dataset...")
    dataset = deduplicate_dataset(dataset)
    dedup_count = total_docs - len(dataset)
    print(f"Removed {dedup_count} duplicate resumes. Unique resumes: {len(dataset)}.")
    
    # 2. Split Dataset
    print("Splitting dataset (80/10/10 split with seed 42)...")
    train, dev, test = split_dataset(dataset)
    print(f"Split sizes: Train={len(train)}, Dev={len(dev)}, Test={len(test)}")
    
    # 3. Convert Splits to DocBins
    print("Converting Train dataset...")
    train_bin, train_stats = convert_to_docbin(train, nlp)
    
    print("Converting Dev dataset...")
    dev_bin, dev_stats = convert_to_docbin(dev, nlp)
    
    print("Converting Test dataset...")
    test_bin, test_stats = convert_to_docbin(test, nlp)
    
    # 4. Save DocBins
    print(f"Saving splits to {processed_dir}...")
    save_docbin(train_bin, train_path)
    save_docbin(dev_bin, dev_path)
    save_docbin(test_bin, test_path)
    
    # Compile statistics
    full_report = {
        "dataset_splits": {
            "train": {
                "size": len(train),
                **train_stats
            },
            "dev": {
                "size": len(dev),
                **dev_stats
            },
            "test": {
                "size": len(test),
                **test_stats
            }
        },
        "totals": {
            "total_raw_resumes": total_docs,
            "total_duplicate_resumes": dedup_count,
            "total_unique_resumes": len(dataset),
            "total_processed_docs": train_stats["processed_docs"] + dev_stats["processed_docs"] + test_stats["processed_docs"],
            "total_raw_annotations": train_stats["total_annotations"] + dev_stats["total_annotations"] + test_stats["total_annotations"],
            "total_valid_spans": train_stats["valid_spans"] + dev_stats["valid_spans"] + test_stats["valid_spans"],
            "total_skipped_invalid_spans": train_stats["skipped_invalid_spans"] + dev_stats["skipped_invalid_spans"] + test_stats["skipped_invalid_spans"],
            "total_filtered_overlapping_spans": train_stats["filtered_overlapping_spans"] + dev_stats["filtered_overlapping_spans"] + test_stats["filtered_overlapping_spans"]
        }
    }
    
    # Print the report
    print("\n" + "="*50)
    print(" DATA PREPARATION PIPELINE REPORT")
    print("="*50)
    print(f"Total Raw Resumes:                {full_report['totals']['total_raw_resumes']}")
    print(f"Duplicate Resumes Removed:        {full_report['totals']['total_duplicate_resumes']}")
    print(f"Unique Resumes:                   {full_report['totals']['total_unique_resumes']}")
    print(f"Total Annotations:                {full_report['totals']['total_raw_annotations']}")
    print(f"Valid Spans (added to DocBin):     {full_report['totals']['total_valid_spans']}")
    print(f"Skipped Invalid Spans:            {full_report['totals']['total_skipped_invalid_spans']}")
    print(f"Filtered Overlapping Spans:       {full_report['totals']['total_filtered_overlapping_spans']}")
    print("-" * 50)
    print("Splits Details:")
    for split_name, stats in full_report["dataset_splits"].items():
        print(f"  {split_name.capitalize()}: {stats['size']} documents")
        print(f"    - Valid Spans: {stats['valid_spans']}")
        print(f"    - Skipped Spans: {stats['skipped_invalid_spans']}")
        print(f"    - Filtered Overlap Spans: {stats['filtered_overlapping_spans']}")
    print("="*50)
    
    # Save report to JSON file
    processed_dir.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=4)
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    main()
