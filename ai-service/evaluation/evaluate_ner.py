from pathlib import Path
import spacy
from spacy.training import Corpus
from spacy.scorer import Scorer

def evaluate():
    # Load trained model (default to model-best, fallback to model-last)
    model_path = Path("trained_models/resume_ner/v1/model-best")
    if not model_path.exists():
        model_path = Path("trained_models/resume_ner/v1/model-last")
        
    if not model_path.exists():
        print(f"Error: Model path not found at {model_path.parent}")
        return

    print(f"Loading trained model from {model_path}...")
    nlp = spacy.load(model_path)

    # Load test corpus
    test_corpus_path = Path("data/processed/test.spacy")
    if not test_corpus_path.exists():
        print(f"Error: Test corpus not found at {test_corpus_path}")
        return
        
    print(f"Loading test corpus from {test_corpus_path}...")
    corpus = Corpus(test_corpus_path)

    # Generate examples (predictions vs gold standard annotations)
    examples = list(corpus(nlp))

    # Evaluate
    print("Running evaluation on test dataset...")
    scores = nlp.evaluate(examples)

    # Extract overall metrics
    ents_p = scores.get("ents_p", 0.0)
    ents_r = scores.get("ents_r", 0.0)
    ents_f = scores.get("ents_f", 0.0)

    # SpaCy 3 scorer returns scores in the range [0.0, 1.0], scale to [0, 100] for readability
    if ents_p is not None and ents_p <= 1.0: ents_p *= 100
    if ents_r is not None and ents_r <= 1.0: ents_r *= 100
    if ents_f is not None and ents_f <= 1.0: ents_f *= 100

    print("=" * 60)
    print("Overall Results")
    print("=" * 60)
    print(f"Precision : {ents_p:.2f}%")
    print(f"Recall    : {ents_r:.2f}%")
    print(f"F1 Score  : {ents_f:.2f}%")

    print("\nPer Label Results")
    print("=" * 60)

    ents_per_type = scores.get("ents_per_type", {})
    for label, values in ents_per_type.items():
        p = values.get("p", 0.0)
        r = values.get("r", 0.0)
        f = values.get("f", 0.0)
        
        # Scale to [0, 100] if necessary
        if p is not None and p <= 1.0: p *= 100
        if r is not None and r <= 1.0: r *= 100
        if f is not None and f <= 1.0: f *= 100
        
        print(
            f"{label:15}"
            f"P={p:.2f}% "
            f"R={r:.2f}% "
            f"F1={f:.2f}%"
        )

if __name__ == "__main__":
    evaluate()
