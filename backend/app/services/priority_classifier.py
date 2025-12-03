import numpy as np
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch

class NLPPriorityClassifier:
    """
    Advanced NLP-based priority classifier using Sentence Transformers
    Uses semantic similarity to classify grievance priority
    """
    
    def __init__(self):
        """Initialize the model (downloads ~80MB first time)"""
        print("🤖 Loading NLP model (this may take a moment)...")
        
        # Use lightweight model optimized for semantic similarity
        # Options: 'all-MiniLM-L6-v2' (fastest), 'paraphrase-MiniLM-L6-v2'
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Define priority templates with semantic descriptions
        self.priority_templates = {
            'CRITICAL': [
                "life threatening emergency situation requires immediate action",
                "death threat murder rape severe violence critical condition",
                "victim is in grave danger needs urgent protection now",
                "medical emergency unconscious bleeding severe injury hospital",
                "immediate threat to life safety critical urgent emergency",
                "accused threatening to kill victim family in danger"
            ],
            'HIGH': [
                "urgent matter needs immediate attention and action",
                "serious threat violence harassment physical assault",
                "victim requires urgent medical treatment hospital care",
                "immediate police protection needed safety concern",
                "urgent compensation required victim in financial crisis",
                "time sensitive matter delayed too long needs quick action"
            ],
            'MEDIUM': [
                "payment compensation delayed pending verification issue",
                "document verification taking longer than expected time",
                "administrative delay processing issue needs resolution",
                "case status not updated waiting for officer response",
                "moderate concern requires attention but not urgent",
                "follow up needed on pending application request"
            ],
            'LOW': [
                "general inquiry question about case status information",
                "routine update request non urgent matter",
                "clarification needed on process documentation",
                "minor issue can wait for resolution",
                "general information query about procedure timeline",
                "non critical administrative question or concern"
            ]
        }
        
        # Precompute embeddings for priority templates
        self.priority_embeddings = self._compute_priority_embeddings()
        
        print("✅ NLP model loaded successfully!")
    
    def _compute_priority_embeddings(self) -> Dict[str, np.ndarray]:
        """Compute and cache embeddings for all priority templates"""
        embeddings = {}
        
        for priority, templates in self.priority_templates.items():
            # Encode all templates for this priority
            template_embeddings = self.model.encode(templates)
            # Use mean embedding as representative
            embeddings[priority] = np.mean(template_embeddings, axis=0)
        
        return embeddings
    def classify_priority(self, title: str, description: str, category: str = "") -> str:
        """
        Classify priority using semantic similarity
        
        Args:
            title: Grievance title
            description: Detailed description
            category: Category/type of grievance
        
        Returns:
            Priority level: CRITICAL, HIGH, MEDIUM, or LOW
        """
        # Combine all text inputs
        text = f"{title}. {description}. {category}".strip()
        
        if not text or len(text) < 10:
            return "LOW"
        
        # Get embedding for the input text
        text_embedding = self.model.encode([text])[0]
        
        # Calculate similarity with each priority
        similarities = {}
        for priority, priority_embedding in self.priority_embeddings.items():
            similarity = cosine_similarity(
                [text_embedding], 
                [priority_embedding]
            )[0][0]
            similarities[priority] = similarity
        
        # Get priority with highest similarity
        best_priority = max(similarities, key=similarities.get)
        best_score = similarities[best_priority]
        
        # Apply confidence threshold
        # If similarity is too low, default to MEDIUM
        if best_score < 0.3:
            return "MEDIUM"
        
        return best_priority
    
    def classify_with_confidence(
        self, 
        title: str, 
        description: str, 
        category: str = ""
    ) -> Dict[str, any]:
        """
        Classify with confidence scores for all priorities
        
        Returns:
            Dictionary with priority and confidence scores
        """
        text = f"{title}. {description}. {category}".strip()
        
        if not text or len(text) < 10:
            return {
                "priority": "LOW",
                "confidence": 0.5,
                "scores": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0.5}
            }
        
        # Get embedding
        text_embedding = self.model.encode([text])[0]
        
        # Calculate similarities
        scores = {}
        for priority, priority_embedding in self.priority_embeddings.items():
            similarity = cosine_similarity(
                [text_embedding], 
                [priority_embedding]
            )[0][0]
            # Convert to 0-1 scale
            scores[priority] = float(max(0, similarity))
        
        # Normalize scores to sum to 1
        total = sum(scores.values())
        if total > 0:
            scores = {k: v/total for k, v in scores.items()}
        
        best_priority = max(scores, key=scores.get)
        confidence = scores[best_priority]
        
        return {
            "priority": best_priority,
            "confidence": round(confidence, 3),
            "scores": {k: round(v, 3) for k, v in scores.items()},
            "explanation": self._get_explanation(best_priority, confidence)
        }
    
    def _get_explanation(self, priority: str, confidence: float) -> str:
        """Generate human-readable explanation"""
        explanations = {
            "CRITICAL": "Contains indicators of life-threatening situation or immediate danger",
            "HIGH": "Indicates urgent matter requiring immediate attention",
            "MEDIUM": "Suggests administrative delay or moderate concern",
            "LOW": "Appears to be general inquiry or routine matter"
        }
        
        confidence_level = "high" if confidence > 0.6 else "moderate" if confidence > 0.4 else "low"
        
        return f"{explanations.get(priority, 'Unknown')} (confidence: {confidence_level})"
    
    def batch_classify(self, texts: List[Tuple[str, str, str]]) -> List[Dict]:
        """
        Classify multiple grievances at once (more efficient)
        
        Args:
            texts: List of (title, description, category) tuples
        
        Returns:
            List of classification results
        """
        results = []
        
        for title, description, category in texts:
            result = self.classify_with_confidence(title, description, category)
            results.append(result)
        
        return results


# Singleton instance
_classifier_instance = None

def get_nlp_classifier() -> NLPPriorityClassifier:
    """Get or create classifier instance (lazy loading)"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = NLPPriorityClassifier()
    return _classifier_instance
