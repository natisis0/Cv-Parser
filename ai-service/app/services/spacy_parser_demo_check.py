import logging
import spacy
from app.services.parser import parse_resume

logger = logging.getLogger(__name__)

_nlp = None

def get_spacy_model():
    global _nlp
    if _nlp is None:
        logger.info("Loading spaCy CV parsing model 'en_cv_info_extr'...")
        _nlp = spacy.load("en_cv_info_extr")
        logger.info("Model loaded successfully.")
    return _nlp


def parse_with_spacy(file_path: str) -> list[dict]:
    # Extract raw text from the file 
    text = parse_resume(file_path)
    
    # Process text using spaCy model
    nlp = get_spacy_model()
    doc = nlp(text)
    
    entities = []
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_,
            "start_char": ent.start_char,
            "end_char": ent.end_char
        })
        
    return entities
