# review_generator.py - Hybrid Personal Review Generator
import random
import re
from typing import Dict, List, Optional

class HybridReviewGenerator:
    """
    Hybrid review generator that creates personalized reviews using customer details
    Combines structured generation with personal touches for maximum uniqueness
    """
    
    def __init__(self):
        # Sentence starters with more variety
        self.openers = [
            "Just had", "Had an amazing", "Visited", "Went to", "Tried", 
            "Finally made it to", "Stopped by", "Discovered", "Decided to try"
        ]
        
        # Occasion-specific language
        self.occasion_language = {
            'date night': {
                'descriptors': ['romantic', 'intimate', 'cozy', 'perfect for couples'],
                'personal_touches': [
                    'my partner and I', 'we both', 'for our', 'date night', 
                    'romantic evening', 'special night out'
                ]
            },
            'family dinner': {
                'descriptors': ['family-friendly', 'welcoming', 'accommodating'],
                'personal_touches': [
                    'the whole family', 'with my kids', 'family loved', 'everyone enjoyed',
                    'even my picky eater', 'kids were happy'
                ]
            },
            'celebration': {
                'descriptors': ['festive', 'special', 'memorable', 'celebratory'],
                'personal_touches': [
                    'celebrating', 'special occasion', 'birthday dinner', 'anniversary',
                    'milestone', 'party of'
                ]
            },
            'business lunch': {
                'descriptors': ['professional', 'convenient', 'efficient'],
                'personal_touches': [
                    'business meeting', 'with colleagues', 'client lunch', 'work meeting',
                    'professional setting', 'good for business'
                ]
            },
            'casual hangout': {
                'descriptors': ['relaxed', 'laid-back', 'comfortable', 'easy-going'],
                'personal_touches': [
                    'with friends', 'casual meal', 'hanging out', 'catching up',
                    'low-key dinner', 'just because'
                ]
            },
            'solo dining': {
                'descriptors': ['comfortable for solo diners', 'welcoming', 'peaceful'],
                'personal_touches': [
                    'dining alone', 'by myself', 'solo meal', 'me time',
                    'peaceful dinner', 'perfect for solo'
                ]
            }
        }
        
        # Words to describe food quality based on rating
        self.food_descriptors = {
            5: ['incredible', 'amazing', 'outstanding', 'phenomenal', 'perfect', 'spectacular'],
            4: ['excellent', 'great', 'wonderful', 'really good', 'delicious', 'impressive']
        }
        
        # Service mentions
        self.service_phrases = [
            'service was excellent', 'staff was friendly', 'servers were attentive',
            'great service', 'staff was helpful', 'service was on point'
        ]
        
        # Closing phrases
        self.closings = [
            "Will definitely be back!", "Can't wait to return!", "Already planning my next visit!",
            "This place is going on my regular rotation!", "Highly recommend!", 
            "Don't sleep on this place!", "Absolutely loved it!"
        ]
    
    def generate_review(self, restaurant, rating: int, favorite_dish: str, atmosphere: str, 
                       special_detail: Optional[str] = None, standout_detail: Optional[str] = None) -> Dict:
        """
        Generate personalized review using customer inputs
        """
        # Parse dishes
        dishes = self._parse_dishes(favorite_dish)
        
        # Generate review components
        components = self._create_review_components(
            restaurant, rating, dishes, atmosphere, special_detail, standout_detail
        )
        
        # Build the review
        review_text = self._build_personalized_review(components)
        
        # Clean up
        review_text = self._cleanup_review(review_text)
        
        # Analyze
        analysis = self._analyze_review(review_text, restaurant.get_seo_keywords())
        
        return {
            'review': review_text,
            'word_count': analysis['word_count'],
            'seo_count': analysis['seo_keywords_used'],
            'seo_keywords': analysis['keywords_found'],
            'personalized': bool(special_detail or standout_detail),
            'uniqueness_score': self._estimate_uniqueness(special_detail, standout_detail)
        }
    
    def _parse_dishes(self, favorite_dish: str) -> List[str]:
        """Parse comma-separated dishes"""
        if not favorite_dish:
            return []
        return [dish.strip() for dish in favorite_dish.split(',') if dish.strip()]
    
    def _create_review_components(self, restaurant, rating: int, dishes: List[str], 
                                atmosphere: str, special_detail: Optional[str], 
                                standout_detail: Optional[str]) -> Dict:
        """Create all review components with personalization"""
        
        occasion_info = self.occasion_language.get(atmosphere, {
            'descriptors': ['nice', 'pleasant'],
            'personal_touches': ['good for', 'nice spot for']
        })
        
        return {
            'opener': self._create_opener(restaurant.name, special_detail, atmosphere),
            'food_section': self._create_food_section(dishes, rating, standout_detail),
            'atmosphere_section': self._create_atmosphere_section(atmosphere, occasion_info),
            'service_mention': random.choice(self.service_phrases),
            'personal_touch': self._create_personal_touch(special_detail, standout_detail),
            'recommendation': self._create_recommendation(restaurant, atmosphere),
            'closing': random.choice(self.closings)
        }
    
    def _create_opener(self, restaurant_name: str, special_detail: Optional[str], atmosphere: str) -> str:
        """Create opening with personal context if available"""
        opener = random.choice(self.openers)
        
        if special_detail:
            # Use the special detail in the opener
            special_clean = special_detail.lower()
            if any(word in special_clean for word in ['birthday', 'anniversary', 'celebration']):
                return f"{opener} {restaurant_name} for {special_detail.lower()}"
            else:
                return f"{opener} {restaurant_name} {special_detail.lower()}"
        else:
            # Generic opener
            return f"{opener} {restaurant_name} {random.choice(['last night', 'today', 'this weekend'])}"
    
    def _create_food_section(self, dishes: List[str], rating: int, standout_detail: Optional[str]) -> str:
        """Create food description with personal details"""
        if not dishes:
            descriptor = random.choice(self.food_descriptors[rating])
            return f"The food was {descriptor}"
        
        # Enhance dish descriptions
        descriptor = random.choice(self.food_descriptors[rating])
        
        if len(dishes) == 1:
            dish_text = dishes[0]
        elif len(dishes) == 2:
            dish_text = f"{dishes[0]} and {dishes[1]}"
        else:
            dish_text = f"{', '.join(dishes[:-1])}, and {dishes[-1]}"
        
        base_text = f"The {dish_text} was absolutely {descriptor}"
        
        # Add standout detail if provided
        if standout_detail:
            return f"{base_text} - {standout_detail.lower()}"
        else:
            return f"{base_text}"
    
    def _create_atmosphere_section(self, atmosphere: str, occasion_info: Dict) -> str:
        """Create atmosphere description"""
        descriptor = random.choice(occasion_info['descriptors'])
        personal_touch = random.choice(occasion_info['personal_touches'])
        
        formats = [
            f"Perfect atmosphere for {atmosphere}, very {descriptor}",
            f"Great spot {personal_touch} - {descriptor} setting",
            f"The ambiance was {descriptor}, ideal for {atmosphere}"
        ]
        
        return random.choice(formats)
    
    def _create_personal_touch(self, special_detail: Optional[str], standout_detail: Optional[str]) -> str:
        """Create additional personal context"""
        if special_detail and standout_detail:
            return f"What made it extra special was {standout_detail.lower()}"
        elif special_detail:
            return f"Perfect choice for {special_detail.lower()}"
        elif standout_detail:
            return f"Loved that {standout_detail.lower()}"
        else:
            return ""
    
    def _create_recommendation(self, restaurant, atmosphere: str) -> str:
        """Create recommendation with SEO integration"""
        seo_keywords = restaurant.get_seo_keywords()
        
        if seo_keywords:
            keyword = random.choice(seo_keywords)
            recommendations = [
                f"Definitely lives up to being {keyword}",
                f"Now I know why it's considered {keyword}",
                f"This is what I think of when I hear '{keyword}'"
            ]
            return random.choice(recommendations)
        else:
            return f"Highly recommend for {atmosphere} or really any occasion"
    
    def _build_personalized_review(self, components: Dict) -> str:
        """Build the complete review from components"""
        
        # Start with opener and food
        review_parts = [
            components['opener'],
            components['food_section']
        ]
        
        # Add atmosphere
        review_parts.append(components['atmosphere_section'])
        
        # Add personal touch if it exists
        if components['personal_touch']:
            review_parts.append(components['personal_touch'])
        
        # Add service mention sometimes
        if random.random() < 0.7:  # 70% chance
            review_parts.append(components['service_mention'])
        
        # Add recommendation
        review_parts.append(components['recommendation'])
        
        # Add closing
        review_parts.append(components['closing'])
        
        return ' '.join(review_parts)
    
    def _cleanup_review(self, review_text: str) -> str:
        """Clean up the review text"""
        # Fix spacing and punctuation
        review_text = re.sub(r'\s+', ' ', review_text)
        review_text = re.sub(r'\s+([.!?])', r'\1', review_text)
        
        # Ensure sentences end with periods
        sentences = review_text.split('. ')
        cleaned_sentences = []
        
        for sentence in sentences:
            if sentence:
                # Capitalize first letter
                sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                cleaned_sentences.append(sentence)
        
        review_text = '. '.join(cleaned_sentences)
        
        # Ensure proper ending
        if not review_text.endswith(('.', '!', '?')):
            review_text += '!'
        
        return review_text.strip()
    
    def _estimate_uniqueness(self, special_detail: Optional[str], standout_detail: Optional[str]) -> float:
        """Estimate uniqueness based on personal details provided"""
        base_score = 0.6  # Base algorithmic uniqueness
        
        if special_detail:
            base_score += 0.2
        if standout_detail:
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    def _analyze_review(self, review_text: str, seo_keywords: List[str]) -> Dict:
        """Analyze the generated review"""
        words = review_text.split()
        word_count = len(words)
        
        # Find SEO keywords used
        keywords_found = []
        review_lower = review_text.lower()
        
        for keyword in seo_keywords:
            if keyword.lower() in review_lower:
                keywords_found.append(keyword)
        
        # Calculate readability
        sentences = len(re.findall(r'[.!?]+', review_text))
        avg_words_per_sentence = word_count / max(sentences, 1)
        readability = "Good" if avg_words_per_sentence < 20 else "Complex"
        
        return {
            'word_count': word_count,
            'seo_keywords_used': len(keywords_found),
            'keywords_found': keywords_found,
            'readability': readability
        }

def create_review_generator():
    """Factory function"""
    return HybridReviewGenerator()