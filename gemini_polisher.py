# gemini_polisher.py - Google Gemini AI Review Polishing Service
import google.generativeai as genai
import os
from typing import Optional

class GeminiReviewPolisher:
    """
    Uses Google Gemini AI to polish restaurant reviews
    Fixes repetition, improves flow, makes text sound more natural
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Gemini API key"""
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        
        if not self.api_key:
            print("Warning: No Gemini API key found. Polishing will be skipped.")
            self.client = None
        else:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel('gemini-2.0-flash')
    
    def polish_review(self, rough_review: str, restaurant_name: str) -> dict:
        """
        Polish a rough review to sound natural and authentic
        
        Args:
            rough_review: The algorithmically generated review
            restaurant_name: Name of the restaurant
            
        Returns:
            Dict with polished review and metadata
        """
        if not self.client:
            # Return original if no API key
            return {
                'polished_review': rough_review,
                'original_review': rough_review,
                'polished': False,
                'cost_estimate': 0
            }
        
        try:
            prompt = self._create_polish_prompt(rough_review, restaurant_name)
            
            # Call Gemini API
            response = self.client.generate_content(prompt)
            polished_text = response.text.strip()
            
            # Calculate approximate cost (very rough estimate)
            input_tokens = len(prompt.split()) * 1.3  # Rough token estimate
            output_tokens = len(polished_text.split()) * 1.3
            cost_estimate = ((input_tokens + output_tokens) / 1000) * 0.000375
            
            return {
                'polished_review': polished_text,
                'original_review': rough_review,
                'polished': True,
                'cost_estimate': cost_estimate,
                'improvement_made': len(polished_text) != len(rough_review)
            }
            
        except Exception as e:
            print(f"Error polishing review: {e}")
            # Return original on error
            return {
                'polished_review': rough_review,
                'original_review': rough_review,
                'polished': False,
                'error': str(e),
                'cost_estimate': 0
            }
    
    def _create_polish_prompt(self, rough_review: str, restaurant_name: str) -> str:
        """Create the prompt for Gemini to polish the review"""
        
        prompt = f"""Polish this restaurant review to sound natural and authentic. Fix any issues but keep the same positive tone and key details. Return ONLY the polished review text, no explanations or formatting.

ISSUES TO FIX:
- Remove repeated phrases or sentences
- Improve sentence flow and transitions
- Make it sound like a real person wrote it
- Fix awkward phrasing
- Ensure varied vocabulary

KEEP THE SAME:
- All specific details (dishes, atmosphere, occasions)
- Positive tone and rating level
- Personal touches and experiences
- Length (around 60-100 words)

RESTAURANT: {restaurant_name}

ORIGINAL REVIEW:
{rough_review}

POLISHED REVIEW:"""

        return prompt

def create_review_polisher() -> GeminiReviewPolisher:
    """Factory function to create review polisher"""
    return GeminiReviewPolisher()