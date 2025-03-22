import spacy
import logging
from typing import List, Dict, Any, Set
from collections import Counter

class KeywordExtractor:
    """Advanced keyword extraction using spaCy for better post relevance."""
    
    def __init__(self, model_name="en_core_web_sm"):
        """Initialize the keyword extractor with the spaCy model."""
        try:
            self.nlp = spacy.load(model_name)
            logging.info(f"Loaded spaCy model: {model_name}")
        except Exception as e:
            logging.error(f"Failed to load spaCy model: {e}")
            raise

    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """
        Extract important keywords from text using spaCy.
        
        Args:
            text: Input text to extract keywords from
            top_n: Number of top keywords to return
            
        Returns:
            List of extracted keywords
        """
        # Process the text with spaCy
        doc = self.nlp(text)
        
        # Extract keywords using different methods
        keywords = []
        
        # Method 1: Extract named entities
        entities = [ent.text.lower() for ent in doc.ents]
        
        # Method 2: Extract noun chunks (noun phrases)
        noun_chunks = [chunk.text.lower() for chunk in doc.noun_chunks]
        
        # Method 3: Extract important words based on POS tags
        # Focus on nouns, proper nouns, and adjectives
        important_words = [token.text.lower() for token in doc 
                        if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and 
                            not token.is_stop and 
                            len(token.text) > 3)]
        
        # Combine all methods and count occurrences
        all_keywords = entities + noun_chunks + important_words
        keyword_counter = Counter(all_keywords)
        
        # Return the top N keywords
        return [keyword for keyword, _ in keyword_counter.most_common(top_n)]

    def extract_keywords_from_question(self, question: str, min_length: int = 2) -> List[str]:
        """
        Extract keywords specifically from a question for search purposes.
        
        Args:
            question: The question to extract keywords from
            min_length: Minimum length of keywords (reduced from 3 to 2)
            
        Returns:
            List of keywords
        """
        # Process with spaCy
        doc = self.nlp(question)
        
        # Extract question focus (what the question is about)
        keywords = set()
        
        # Get entities
        for ent in doc.ents:
            if len(ent.text) >= min_length:
                keywords.add(ent.text.lower())
        
        # Get noun chunks
        for chunk in doc.noun_chunks:
            if len(chunk.text) >= min_length:
                keywords.add(chunk.text.lower())
        
        # Get important individual tokens
        for token in doc:
            # Skip stopwords, short words, and non-relevant parts of speech
            if (token.is_stop or len(token.text) < min_length or 
                token.pos_ not in ['NOUN', 'PROPN', 'ADJ', 'VERB']):
                continue
                
            # Skip common question words
            if token.text.lower() in ['what', 'when', 'where', 'who', 'why', 'how']:
                continue
                
            keywords.add(token.text.lower())
        
        # Special case for acronyms and important short words
        special_terms = ["ai", "ml", "ui", "ux", "vr", "ar"]
        for term in special_terms:
            if term in question.lower():
                keywords.add(term)
        
        return list(keywords)
