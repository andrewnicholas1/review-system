# review_generator.py - Smart Review Generation Engine
import random
import re
from typing import Dict, List, Tuple

class ReviewGenerator:
    """
    Smart review generation engine that creates SEO-optimized reviews
    using restaurant templates, customer input, and AI-driven variation
    """
    
    def __init__(self):
        self.cuisine_praise = {
            "Mexican": [
                "authentic flavors that transported me straight to Mexico",
                "fresh ingredients with the perfect balance of spices", 
                "traditional preparation with incredible taste",
                "genuine Mexican flavors done right",
                "bold spices and amazing presentation",
                "like my abuela's cooking but even better"
            ],
            "Italian": [
                "traditional Italian techniques with premium ingredients",
                "perfectly prepared with authentic Italian flair", 
                "like dining in Tuscany with incredible attention to detail",
                "masterfully crafted with genuine Italian passion",
                "rich, authentic flavors that sing",
                "perfectly al dente with amazing sauce"
            ],
            "Chinese": [
                "authentic Chinese flavors with perfect seasoning",
                "traditional techniques with fresh ingredients",
                "amazing wok hei and perfect balance of flavors"
            ],
            "American": [
                "perfectly prepared comfort food",
                "classic American flavors done exceptionally well",
                "hearty portions with incredible taste"
            ],
            "Thai": [
                "perfect balance of sweet, sour, salty and spicy",
                "authentic Thai flavors with amazing aromatics",
                "traditional recipes with fresh herbs and spices"
            ]
        }
        
        self.closing_phrases = {
            "casual": [
                "Can't wait to come back and try more dishes!",
                "Already planning my next visit!",
                "This place is definitely going on my regular rotation!",
                "Telling all my friends about this gem!",
                "Will definitely be back soon!",
                "Highly recommend to anyone in the area!"
            ],
            "upscale": [
                "We look forward to returning for another exceptional experience.",
                "A dining experience we will fondly remember.",
                "This establishment has earned our highest recommendation.",
                "We will certainly be returning guests.",
                "An outstanding addition to the culinary landscape.",
                "Exceptional in every regard."
            ],
            "fast_casual": [
                "Perfect for a quick, delicious meal!",
                "Great option when you want quality fast food!",
                "Will definitely be back when I'm in the area!",
                "Exactly what I was looking for!"
            ]
        }
    
    def generate_review(self, restaurant, rating: int, favorite_dish: str, atmosphere: str) -> Dict:
        """
        Generate a complete review using restaurant data and customer input
        
        Args:
            restaurant: Restaurant model instance
            rating: Customer rating (1-5)
            favorite_dish: Customer's favorite dish
            atmosphere: Dining occasion/atmosphere
            
        Returns:
            Dict with review text, word count, and SEO analysis
        """
        
        # Get restaurant templates or use defaults
        templates = restaurant.get_custom_templates()
        if not templates:
            templates = self._get_default_templates(restaurant.restaurant_type)
        
        # Select random template
        template = random.choice(templates)
        
        # Prepare template variables
        template_vars = self._prepare_template_variables(
            restaurant, rating, favorite_dish, atmosphere
        )
        
        # Generate review text
        review_text = template.format(**template_vars)
        
        # Clean and enhance the review
        review_text = self._enhance_review(review_text)
        
        # Analyze the review
        analysis = self._analyze_review(review_text, restaurant.get_seo_keywords())
        
        return {
            'review': review_text,
            'word_count': analysis['word_count'],
            'seo_count': analysis['seo_keywords_used'],
            'seo_keywords': analysis['keywords_found'],
            'readability_score': analysis['readability'],
            'template_used': templates.index(template) + 1
        }
    
    def _prepare_template_variables(self, restaurant, rating: int, favorite_dish: str, atmosphere: str) -> Dict:
        """Prepare all variables needed for template formatting"""
        
        # Get and shuffle SEO keywords for variety
        seo_keywords = restaurant.get_seo_keywords().copy()
        random.shuffle(seo_keywords)
        
        # Get cuisine-specific praise
        cuisine_praise = self._get_cuisine_praise(restaurant.cuisine)
        
        # Get appropriate closing phrase
        closing_phrase = self._get_closing_phrase(restaurant.restaurant_type)
        
        # Enhance favorite dish description
        enhanced_dish = self._enhance_dish_description(favorite_dish, restaurant.cuisine)
        
        return {
            'name': restaurant.name,
            'rating': rating,
            'dish': enhanced_dish,
            'favorite_dish': enhanced_dish,  # Alternative name
            'atmosphere': atmosphere,
            'location': restaurant.location,
            'cuisine': restaurant.cuisine,
            'cuisine_praise': cuisine_praise,
            'seo_keyword_1': seo_keywords[0] if seo_keywords else f"great {restaurant.cuisine.lower()} restaurant",
            'seo_keyword_2': seo_keywords[1] if len(seo_keywords) > 1 else seo_keywords[0] if seo_keywords else f"{restaurant.cuisine.lower()} food",
            'closing_praise': closing_phrase,
            'restaurant_type': restaurant.restaurant_type
        }
    
    def _get_cuisine_praise(self, cuisine: str) -> str:
        """Get random cuisine-specific praise phrase"""
        praise_options = self.cuisine_praise.get(cuisine, [
            "perfectly prepared with great attention to detail",
            "absolutely delicious with amazing flavors",
            "expertly crafted and beautifully presented"
        ])
        return random.choice(praise_options)
    
    def _get_closing_phrase(self, restaurant_type: str) -> str:
        """Get appropriate closing phrase based on restaurant type"""
        phrases = self.closing_phrases.get(restaurant_type, self.closing_phrases['casual'])
        return random.choice(phrases)
    
    def _enhance_dish_description(self, dish: str, cuisine: str) -> str:
        """Add cuisine-specific enhancements to dish names"""
        dish_lower = dish.lower()
        
        # Cuisine-specific dish enhancements
        enhancements = {
            'Mexican': {
                'tacos': ['amazing tacos', 'authentic tacos', 'incredible tacos'],
                'burrito': ['massive burrito', 'loaded burrito', 'perfect burrito'],
                'enchiladas': ['cheese enchiladas', 'chicken enchiladas', 'amazing enchiladas'],
                'margarita': ['perfect margarita', 'refreshing margarita', 'house margarita']
            },
            'Italian': {
                'pasta': ['homemade pasta', 'fresh pasta', 'perfectly cooked pasta'],
                'pizza': ['wood-fired pizza', 'authentic pizza', 'amazing pizza'],
                'risotto': ['creamy risotto', 'perfect risotto', 'incredible risotto']
            }
        }
        
        cuisine_enhancements = enhancements.get(cuisine, {})
        
        for key_dish, enhanced_options in cuisine_enhancements.items():
            if key_dish in dish_lower:
                return random.choice(enhanced_options)
        
        # Default enhancement
        return dish if len(dish.split()) > 1 else f"amazing {dish}"
    
    def _enhance_review(self, review_text: str) -> str:
        """Clean up and enhance the generated review"""
        
        # Fix common formatting issues
        review_text = re.sub(r'\s+', ' ', review_text)  # Multiple spaces
        review_text = re.sub(r'\s+([.!?])', r'\1', review_text)  # Spaces before punctuation
        review_text = review_text.strip()
        
        # Ensure proper capitalization
        sentences = review_text.split('. ')
        enhanced_sentences = []
        
        for sentence in sentences:
            if sentence:
                # Capitalize first letter of each sentence
                sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                enhanced_sentences.append(sentence)
        
        review_text = '. '.join(enhanced_sentences)
        
        # Ensure proper ending punctuation
        if not review_text.endswith(('.', '!', '?')):
            review_text += '!'
        
        return review_text
    
    def _analyze_review(self, review_text: str, seo_keywords: List[str]) -> Dict:
        """Analyze the generated review for SEO and quality metrics"""
        
        words = review_text.split()
        word_count = len(words)
        
        # Find SEO keywords used
        keywords_found = []
        review_lower = review_text.lower()
        
        for keyword in seo_keywords:
            if keyword.lower() in review_lower:
                keywords_found.append(keyword)
        
        # Calculate basic readability (simplified)
        sentences = len(re.findall(r'[.!?]+', review_text))
        avg_words_per_sentence = word_count / max(sentences, 1)
        
        # Simple readability score (lower is better)
        readability = "Good" if avg_words_per_sentence < 20 else "Complex"
        
        return {
            'word_count': word_count,
            'seo_keywords_used': len(keywords_found),
            'keywords_found': keywords_found,
            'readability': readability,
            'sentences': sentences,
            'avg_words_per_sentence': round(avg_words_per_sentence, 1)
        }
    
    def _get_default_templates(self, restaurant_type: str) -> List[str]:
        """Get default templates when restaurant hasn't customized theirs"""
        
        templates = {
            'casual': [
                "Had an amazing {rating}-star experience at {name}! The {dish} was absolutely incredible - {cuisine_praise}. Perfect spot for {atmosphere} and definitely {seo_keyword_1}. The {location} location is super convenient! {closing_praise}",
                
                "Wow! {name} totally exceeded my expectations! The {dish} was fantastic - {cuisine_praise}. Great atmosphere for {atmosphere}, and honestly one of the {seo_keyword_2} around. {closing_praise}",
                
                "Just discovered my new favorite place! {name} serves amazing {rating}-star {cuisine} food. The {dish} was the highlight - {cuisine_praise}. Perfect for {atmosphere} and easily {seo_keyword_1}. {closing_praise}"
            ],
            
            'upscale': [
                "Exceptional {rating}-star dining experience at {name}. The {dish} was expertly prepared - {cuisine_praise}. The ambiance was perfect for {atmosphere}, truly representing {seo_keyword_1}. The {location} location adds to its sophisticated charm. {closing_praise}",
                
                "Outstanding evening at {name}. The {dish} was beautifully crafted - {cuisine_praise}. Every detail made it ideal for {atmosphere}. When seeking {seo_keyword_2}, this restaurant delivers excellence. {closing_praise}",
                
                "Remarkable {rating}-star experience at {name}. The {dish} showcased culinary expertise - {cuisine_praise}. Wonderful setting for {atmosphere} with impeccable service throughout. Easily {seo_keyword_1} with its commitment to quality. {closing_praise}"
            ],
            
            'fast_casual': [
                "Great {rating}-star experience at {name}! The {dish} was delicious and quick - {cuisine_praise}. Perfect for {atmosphere} when you want quality food fast. Definitely {seo_keyword_1} for the area! {closing_praise}",
                
                "Really impressed with {name}! The {dish} was amazing - {cuisine_praise}. Great option for {atmosphere} and one of the {seo_keyword_2} spots around. {closing_praise}"
            ]
        }
        
        return templates.get(restaurant_type, templates['casual'])

# Convenience function for easy import
def create_review_generator() -> ReviewGenerator:
    """Factory function to create review generator"""
    return ReviewGenerator()