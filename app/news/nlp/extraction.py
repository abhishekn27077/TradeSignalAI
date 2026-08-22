import re


class KeywordExtraction:
    """
    Extracts relevant keywords from text using frequency or heuristics.
    """
    STOP_WORDS = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"}

    @staticmethod
    def extract(text: str, top_n: int = 5) -> list:
        # Simple extraction based on word frequency
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        freq = {}
        for w in words:
            if w not in KeywordExtraction.STOP_WORDS:
                freq[w] = freq.get(w, 0) + 1
        
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:top_n]]

class NamedEntityRecognition:
    """
    Extracts Named Entities (Companies, People, Locations).
    Fallback heuristic uses capitalized words not at the start of sentences.
    """
    @staticmethod
    def extract(text: str) -> list:
        # Very basic heuristic for capitalized words
        # In prod: use spaCy or transformers
        entities = re.findall(r'\b[A-Z][a-z]+\b', text)
        return list(set(entities))
