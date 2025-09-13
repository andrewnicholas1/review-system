# google_places.py - Google Places API Integration
import googlemaps
import os
from typing import Dict, Optional, List
import re

class GooglePlacesService:
    """
    Service to interact with Google Places API
    Fetches restaurant data without requiring approval
    """
    
    def __init__(self, api_key: str = None):
        """Initialize with Google Places API key"""
        self.api_key = api_key or os.environ.get('GOOGLE_PLACES_API_KEY')
        
        if not self.api_key:
            print("⚠️ Warning: No Google Places API key found. Using mock data.")
            self.client = None
        else:
            self.client = googlemaps.Client(key=self.api_key)
    
    def search_restaurant(self, query: str, location: str = None) -> List[Dict]:
        """
        Search for restaurants by name and location
        Returns list of potential matches
        """
        if not self.client:
            return self._mock_search_results(query)
        
        try:
            # Construct search query
            search_query = f"{query} restaurant"
            if location:
                search_query += f" {location}"
            
            # Use Places API text search
            results = self.client.places(
                query=search_query,
                type='restaurant'
            )
            
            restaurants = []
            for place in results.get('results', [])[:5]:  # Limit to top 5
                restaurant_data = self._extract_place_data(place)
                if restaurant_data:
                    restaurants.append(restaurant_data)
            
            return restaurants
            
        except Exception as e:
            print(f"Error searching restaurants: {e}")
            return self._mock_search_results(query)
    
    def get_restaurant_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed restaurant information by place_id
        This is what we use to populate our database
        """
        if not self.client:
            return self._mock_restaurant_details(place_id)
        
        try:
            # Get detailed place information
            result = self.client.place(
                place_id=place_id,
                fields=[
                    'name', 'formatted_address', 'formatted_phone_number',
                    'website', 'rating', 'user_ratings_total', 'reviews',
                    'opening_hours', 'types', 'photos', 'price_level',
                    'geometry', 'place_id', 'plus_code'
                ]
            )
            
            place = result.get('result', {})
            return self._extract_detailed_place_data(place)
            
        except Exception as e:
            print(f"Error getting restaurant details: {e}")
            return self._mock_restaurant_details(place_id)
    
    def _extract_place_data(self, place: Dict) -> Dict:
        """Extract basic data from Places API search result"""
        return {
            'place_id': place.get('place_id'),
            'name': place.get('name'),
            'address': place.get('formatted_address', ''),
            'rating': place.get('rating', 0),
            'price_level': place.get('price_level', 0),
            'types': place.get('types', [])
        }
    
    def _extract_detailed_place_data(self, place: Dict) -> Dict:
        """Extract detailed data for restaurant creation"""
        
        # Extract location info
        location = self._extract_location_from_address(
            place.get('formatted_address', '')
        )
        
        # Determine cuisine type from Google categories
        cuisine = self._determine_cuisine_type(place.get('types', []))
        
        # Extract restaurant type (casual/upscale) from price level and types
        restaurant_type = self._determine_restaurant_type(
            place.get('price_level', 1),
            place.get('types', [])
        )
        
        # Generate suggested specialties from reviews
        specialties = self._extract_specialties_from_reviews(
            place.get('reviews', [])
        )
        
        # Generate SEO keywords
        seo_keywords = self._generate_seo_keywords(
            place.get('name', ''),
            cuisine,
            location
        )
        
        return {
            # Basic Google data
            'google_place_id': place.get('place_id'),
            'name': place.get('name'),
            'address': place.get('formatted_address'),
            'phone': place.get('formatted_phone_number'),
            'website': place.get('website'),
            'google_rating': place.get('rating'),
            'google_review_count': place.get('user_ratings_total', 0),
            
            # Processed data for our system
            'location': location,
            'cuisine': cuisine,
            'restaurant_type': restaurant_type,
            'suggested_specialties': specialties,
            'suggested_seo_keywords': seo_keywords,
            
            # Additional data
            'price_level': place.get('price_level', 1),
            'google_types': place.get('types', []),
            'hours': self._extract_hours(place.get('opening_hours', {})),
            
            # Generate Google review link
            'google_review_link': self._generate_review_link(place.get('place_id'))
        }
    
    def _extract_location_from_address(self, address: str) -> str:
        """Extract city/neighborhood from formatted address"""
        if not address:
            return "local area"
        
        # Split address and get city (usually second to last component)
        parts = address.split(', ')
        if len(parts) >= 2:
            # Remove state abbreviation and ZIP if present
            city_part = parts[-3] if len(parts) > 2 else parts[-2]
            return city_part.strip()
        
        return "local area"
    
    def _determine_cuisine_type(self, types: List[str]) -> str:
        """Map Google place types to cuisine types"""
        
        cuisine_mapping = {
            'mexican_restaurant': 'Mexican',
            'italian_restaurant': 'Italian',
            'chinese_restaurant': 'Chinese',
            'thai_restaurant': 'Thai',
            'indian_restaurant': 'Indian',
            'japanese_restaurant': 'Japanese',
            'french_restaurant': 'French',
            'american_restaurant': 'American',
            'pizza_restaurant': 'Pizza',
            'seafood_restaurant': 'Seafood',
            'steak_house': 'Steakhouse',
            'fast_food_restaurant': 'Fast Food'
        }
        
        for place_type in types:
            if place_type in cuisine_mapping:
                return cuisine_mapping[place_type]
        
        # If no specific cuisine found, return generic
        return 'Restaurant'
    
    def _determine_restaurant_type(self, price_level: int, types: List[str]) -> str:
        """Determine restaurant type (casual/upscale) from price and categories"""
        
        # Check for upscale indicators
        upscale_types = ['fine_dining_restaurant', 'wine_bar', 'cocktail_bar']
        if any(t in types for t in upscale_types):
            return 'upscale'
        
        # Check for casual indicators  
        casual_types = ['fast_food_restaurant', 'fast_casual_restaurant', 'sports_bar']
        if any(t in types for t in casual_types):
            return 'casual'
        
        # Use price level (0-4 scale where 4 is most expensive)
        if price_level >= 3:
            return 'upscale'
        elif price_level <= 1:
            return 'fast_casual'
        else:
            return 'casual'
    
    def _extract_specialties_from_reviews(self, reviews: List[Dict]) -> List[str]:
        """Extract popular dishes mentioned in Google reviews"""
        specialties = set()
        
        # Common food terms to look for
        food_terms = [
            'pizza', 'pasta', 'burger', 'tacos', 'burrito', 'sandwich',
            'salad', 'soup', 'steak', 'chicken', 'fish', 'salmon',
            'wings', 'fries', 'dessert', 'cake', 'ice cream', 'cocktail',
            'margarita', 'beer', 'wine', 'coffee', 'bread', 'cheese'
        ]
        
        for review in reviews:
            text = review.get('text', '').lower()
            for term in food_terms:
                if term in text and len(specialties) < 5:
                    specialties.add(term)
        
        return list(specialties) or ['signature dish', 'daily special']
    
    def _generate_seo_keywords(self, name: str, cuisine: str, location: str) -> List[str]:
        """Generate SEO keywords based on restaurant data"""
        
        keywords = []
        
        # Location-based keywords
        keywords.append(f"best {cuisine.lower()} restaurant {location.lower()}")
        keywords.append(f"{cuisine.lower()} food near me")
        keywords.append(f"top {cuisine.lower()} {location.lower()}")
        
        # Name-based keyword
        if name:
            first_word = name.split()[0].lower()
            keywords.append(f"{first_word} restaurant {location.lower()}")
        
        # Occasion-based keywords
        keywords.extend([
            f"date night restaurant {location.lower()}",
            f"family restaurant {location.lower()}",
            f"lunch {location.lower()}"
        ])
        
        return keywords[:6]  # Limit to 6 keywords
    
    def _extract_hours(self, opening_hours: Dict) -> str:
        """Extract and format opening hours"""
        weekday_text = opening_hours.get('weekday_text', [])
        return '; '.join(weekday_text) if weekday_text else 'Hours not available'
    
    def _generate_review_link(self, place_id: str) -> str:
        """Generate Google review link from place_id"""
        if not place_id:
            return ''
        
        return f"https://search.google.com/local/writereview?placeid={place_id}"
    
    # Mock data methods for testing without API key
    def _mock_search_results(self, query: str) -> List[Dict]:
        """Return mock search results for testing"""
        return [
            {
                'place_id': 'mock_pablos_123',
                'name': f"{query} (Mock Result)",
                'address': '123 Main St, Seattle, WA, USA',
                'rating': 4.3,
                'price_level': 2,
                'types': ['mexican_restaurant', 'restaurant']
            }
        ]
    
    def _mock_restaurant_details(self, place_id: str) -> Dict:
        """Return mock restaurant details for testing"""
        return {
            'google_place_id': place_id,
            'name': 'Mock Restaurant (No API Key)',
            'address': '123 Test Street, Seattle, WA 98101, USA',
            'phone': '(206) 555-0123',
            'website': 'https://example.com',
            'google_rating': 4.2,
            'google_review_count': 150,
            'location': 'Seattle',
            'cuisine': 'Mexican',
            'restaurant_type': 'casual',
            'suggested_specialties': ['tacos', 'margaritas', 'guacamole'],
            'suggested_seo_keywords': [
                'best mexican restaurant seattle',
                'mexican food near me',
                'date night restaurant seattle'
            ],
            'price_level': 2,
            'google_types': ['mexican_restaurant', 'restaurant'],
            'hours': 'Mon-Sun: 11:00 AM - 10:00 PM',
            'google_review_link': 'https://search.google.com/local/writereview?placeid=mock'
        }

# Convenience function for easy import
def create_places_service() -> GooglePlacesService:
    """Factory function to create Places service"""
    return GooglePlacesService()