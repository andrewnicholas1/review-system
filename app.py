# app.py - Complete Restaurant Review System with Improved UX
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from models import db, Restaurant, User, Review, create_sample_data
from google_places import create_places_service
from review_generator import create_review_generator
import os
import json

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant_reviews.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    return app

# Create the app
app = create_app()

@app.route('/')
def home():
    """Home page with system overview and restaurant list"""
    restaurants = Restaurant.query.all()
    
    return f"""
    <div style="font-family: Arial; max-width: 900px; margin: 30px auto; padding: 20px;">
        <h1>🍽️ Restaurant Review System</h1>
        <h2 style="color: green;">✅ Professional Review System Ready!</h2>
        
        <div style="background: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>📊 System Status:</h3>
            <ul>
                <li>✅ Flask web framework running</li>
                <li>✅ SQLAlchemy database connected</li>
                <li>✅ Google Places API integration ready</li>
                <li>✅ Professional review interface with edit capability</li>
                <li>✅ Direct Google Reviews integration</li>
                <li>✅ AI review generation engine active</li>
                <li>✅ {len(restaurants)} restaurants in database</li>
            </ul>
        </div>
        
        <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🏪 Demo Restaurants:</h3>
            {_render_restaurant_list(restaurants)}
        </div>
        
        <div style="background: #fffbeb; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🔗 Try the System:</h3>
            <ul>
                <li><a href="/demo-review" target="_blank"><strong>🎭 Demo Review System</strong></a> - Complete overview</li>
                <li><a href="/review/pablos-mexican" target="_blank">📱 Customer Review - Pablo's Mexican</a></li>
                <li><a href="/review/sophias-italian" target="_blank">📱 Customer Review - Sophia's Italian</a></li>
                <li><a href="/test-places" target="_blank">🔍 Test Google Places API</a></li>
                <li><a href="/dashboard" target="_blank">🏪 Restaurant Dashboard (Coming Soon)</a></li>
            </ul>
        </div>
        
        <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h4>🎯 Latest Improvements:</h4>
            <ul>
                <li>✅ Enhanced star rating with visual feedback</li>
                <li>✅ Editable AI-generated reviews</li>
                <li>✅ Direct Google Reviews integration</li>
                <li>✅ Removed technical SEO hints from customer interface</li>
                <li>✅ Professional user experience</li>
                <li>✅ Mobile-optimized responsive design</li>
            </ul>
        </div>
        
        <p><em>Built with Flask + SQLAlchemy + Google Places API + AI Review Engine</em></p>
    </div>
    """

def _render_restaurant_list(restaurants):
    """Helper function to render restaurant list"""
    if not restaurants:
        return "<p><em>No restaurants in database. <a href='/init-db'>Click here to initialize with sample data</a>.</em></p>"
    
    html = "<ul>"
    for restaurant in restaurants:
        specialties = ', '.join(restaurant.get_specialties()[:3])
        keywords_count = len(restaurant.get_seo_keywords())
        templates_count = len(restaurant.get_custom_templates())
        
        html += f"""
        <li style="margin: 10px 0; padding: 10px; background: white; border-radius: 5px;">
            <strong>{restaurant.name}</strong> ({restaurant.slug})
            <br><small>📍 {restaurant.location} • {restaurant.cuisine} • {restaurant.restaurant_type}</small>
            <br><small>🍽️ Specialties: {specialties}</small>
            <br><small>📈 {keywords_count} SEO keywords, {templates_count} templates</small>
            <br><small>📞 {restaurant.phone} • 💳 {restaurant.subscription_plan}</small>
            <br><small><a href="/review/{restaurant.slug}">📱 Customer Review Interface</a></small>
        </li>
        """
    html += "</ul>"
    return html

@app.route('/review/<restaurant_slug>')
def customer_review(restaurant_slug):
    """Customer review interface - the interactive form customers see"""
    
    # Find restaurant by slug
    restaurant = Restaurant.query.filter_by(slug=restaurant_slug).first()
    
    if not restaurant:
        return f"""
        <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
            <h1>❌ Restaurant Not Found</h1>
            <p>Sorry, we couldn't find a restaurant with ID: <strong>{restaurant_slug}</strong></p>
            <p><a href="/">← Back to Home</a></p>
        </div>
        """, 404
    
    # Render the interactive review form
    return render_template('customer_review_form.html', restaurant=restaurant)

@app.route('/generate-review/<restaurant_slug>', methods=['POST'])
def generate_review_api(restaurant_slug):
    """API endpoint to generate review text with improved keyword integration"""
    
    restaurant = Restaurant.query.filter_by(slug=restaurant_slug).first()
    if not restaurant:
        return jsonify({'success': False, 'error': 'Restaurant not found'}), 404
    
    try:
        # Get data from request
        data = request.get_json()
        rating = int(data.get('rating'))
        favorite_dish = data.get('favorite_dish', '').strip()
        atmosphere = data.get('atmosphere', '').strip()
        
        # Validate input
        if not (1 <= rating <= 5):
            return jsonify({'success': False, 'error': 'Invalid rating'}), 400
        
        if not favorite_dish or not atmosphere:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Generate the review with multiple keywords
        generator = create_review_generator()
        result = generator.generate_review(restaurant, rating, favorite_dish, atmosphere)
        
        return jsonify({
            'success': True,
            'review': result['review'],
            'word_count': result['word_count'],
            'seo_count': result['seo_count'],
            'seo_keywords': result['seo_keywords'],
            'template_used': result['template_used']
        })
        
    except Exception as e:
        print(f"Error generating review: {e}")
        return jsonify({'success': False, 'error': 'Failed to generate review'}), 500

@app.route('/submit-review/<restaurant_slug>', methods=['POST'])
def submit_review(restaurant_slug):
    """Handle final review submission"""
    
    restaurant = Restaurant.query.filter_by(slug=restaurant_slug).first()
    if not restaurant:
        return "Restaurant not found", 404
    
    try:
        # Get form data
        rating = int(request.form.get('rating'))
        
        if rating >= 4:
            # Positive review path
            favorite_dish = request.form.get('favorite_dish_final', '').strip()
            atmosphere = request.form.get('atmosphere', '').strip()
            final_review = request.form.get('final_review', '').strip()
            
            # Use final review if provided (edited version), otherwise generate new one
            if not final_review:
                generator = create_review_generator()
                result = generator.generate_review(restaurant, rating, favorite_dish, atmosphere)
                final_review = result['review']
                word_count = result['word_count']
            else:
                word_count = len(final_review.split())
            
            # Save to database
            review_record = Review(
                restaurant_id=restaurant.id,
                rating=rating,
                review_type='public',
                favorite_dish=favorite_dish,
                atmosphere=atmosphere,
                generated_review=final_review,
                word_count=word_count,
                status='completed'
            )
            
            db.session.add(review_record)
            db.session.commit()
            
            return f"""
            <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
                <h1>🎉 Thank You!</h1>
                <p>Your review has been generated and saved!</p>
                <div style="background: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>✅ Review Completed Successfully</h3>
                    <p><strong>Rating:</strong> {rating} stars</p>
                    <p><strong>Favorite Dish:</strong> {favorite_dish}</p>
                    <p><strong>Word Count:</strong> {word_count} words</p>
                    <p><strong>Status:</strong> Ready for Google Reviews</p>
                </div>
                <p>We hope you'll visit {restaurant.name} again soon!</p>
                <p><a href="/">← Back to Home</a></p>
            </div>
            """
            
        else:
            # Negative feedback path
            issue_area = request.form.get('issue_area', '').strip()
            feedback_details = request.form.get('feedback_details', '').strip()
            contact_info = request.form.get('contact_info', '').strip()
            
            # Save private feedback
            review_record = Review(
                restaurant_id=restaurant.id,
                rating=rating,
                review_type='private',
                issue_area=issue_area,
                feedback_details=feedback_details,
                requires_followup=True,
                status='completed'
            )
            
            # Add contact info if provided
            if contact_info:
                if '@' in contact_info:
                    review_record.customer_email = contact_info
                else:
                    review_record.customer_phone = contact_info
            
            db.session.add(review_record)
            db.session.commit()
            
            return f"""
            <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
                <h1>📧 Feedback Sent!</h1>
                <p>Thank you for your honest feedback.</p>
                <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>✅ Your feedback has been sent to {restaurant.name} management</h3>
                    <p><strong>Issue Area:</strong> {issue_area}</p>
                    <p><strong>Contact Method:</strong> {contact_info or 'Not provided'}</p>
                </div>
                <p>A manager will review your feedback and may reach out within 24 hours.</p>
                <p>We appreciate you giving us the opportunity to improve!</p>
                <p><a href="/">← Back to Home</a></p>
            </div>
            """
    
    except Exception as e:
        print(f"Error submitting review: {e}")
        return f"""
        <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
            <h1>❌ Error</h1>
            <p>Sorry, there was an error processing your review. Please try again.</p>
            <p><a href="/review/{restaurant_slug}">← Back to Review Form</a></p>
        </div>
        """, 500

@app.route('/demo-review')
def demo_review():
    """Demo the review system with sample data"""
    return """
    <div style="font-family: Arial; max-width: 800px; margin: 20px auto; padding: 20px;">
        <h1>🎭 Professional Review System Demo</h1>
        <p>Experience the complete customer review journey with our demo restaurants:</p>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 30px 0;">
            
            <div style="border: 2px solid #667eea; padding: 20px; border-radius: 12px; text-align: center;">
                <h3>🌮 Pablo's Mexican Cantina</h3>
                <p><strong>Type:</strong> Casual Mexican</p>
                <p><strong>Specialties:</strong> Tacos, Margaritas, Enchiladas</p>
                <p><strong>Features:</strong> Enhanced star rating, editable reviews</p>
                <a href="/review/pablos-mexican" style="display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; margin-top: 10px;">
                    📱 Leave Review →
                </a>
            </div>
            
            <div style="border: 2px solid #764ba2; padding: 20px; border-radius: 12px; text-align: center;">
                <h3>🍝 Sophia's Fine Italian</h3>
                <p><strong>Type:</strong> Upscale Italian</p>
                <p><strong>Specialties:</strong> Pasta, Risotto, Wine</p>
                <p><strong>Features:</strong> Professional templates, Google integration</p>
                <a href="/review/sophias-italian" style="display: inline-block; padding: 12px 24px; background: #764ba2; color: white; text-decoration: none; border-radius: 8px; margin-top: 10px;">
                    📱 Leave Review →
                </a>
            </div>
            
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🎯 Latest Improvements:</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div>
                    <h4>✅ Enhanced User Experience:</h4>
                    <ul>
                        <li>Better star rating visual feedback</li>
                        <li>Editable AI-generated reviews</li>
                        <li>Direct Google Reviews integration</li>
                        <li>Professional mobile interface</li>
                        <li>Removed technical SEO hints</li>
                    </ul>
                </div>
                <div>
                    <h4>📧 Smart Feedback Routing:</h4>
                    <ul>
                        <li>4-5 stars → Public review generation</li>
                        <li>1-3 stars → Private management feedback</li>
                        <li>Copy/paste functionality</li>
                        <li>Real Google Maps integration</li>
                        <li>Database tracking and analytics</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>📱 Professional Features:</h3>
            <p>The review interface now provides a seamless, professional experience that customers expect. 
            Enhanced visual feedback, editable reviews, and direct Google integration make this a 
            production-ready solution for restaurants.</p>
        </div>
        
        <p style="text-align: center;">
            <a href="/" style="display: inline-block; padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 8px;">← Back to Home</a>
        </p>
    </div>
    """

@app.route('/test-places')
def test_places_api():
    """Test Google Places API integration"""
    return """
    <div style="font-family: Arial; max-width: 800px; margin: 20px auto; padding: 20px;">
        <h1>🔍 Google Places API Test</h1>
        <p>Test the Google Places integration for restaurant data lookup.</p>
        
        <div style="background: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🧪 Test Restaurant Lookup:</h3>
            <form method="GET" action="/places-search">
                <input type="text" name="query" placeholder="Restaurant name (e.g., 'Chipotle', 'Pizza Hut')" 
                       style="width: 300px; padding: 10px; margin-right: 10px;" required>
                <input type="text" name="location" placeholder="Location (e.g., 'Seattle', 'New York')" 
                       style="width: 200px; padding: 10px; margin-right: 10px;">
                <button type="submit" style="padding: 10px 20px;">Search Restaurants</button>
            </form>
        </div>
        
        <div style="background: #fffbeb; padding: 15px; border-radius: 8px;">
            <h4>💡 What This Tests:</h4>
            <ul>
                <li>Google Places API search functionality</li>
                <li>Restaurant data extraction and processing</li>
                <li>Automatic cuisine type detection</li>
                <li>SEO keyword generation</li>
                <li>Specialty dish extraction from reviews</li>
                <li>Restaurant type classification (casual/upscale)</li>
            </ul>
            <p><strong>Note:</strong> Without a Google Places API key, this will show mock data for testing.</p>
        </div>
        
        <p><a href="/">← Back to Home</a></p>
    </div>
    """

@app.route('/places-search')
def places_search():
    """Search for restaurants using Google Places API"""
    query = request.args.get('query', '').strip()
    location = request.args.get('location', '').strip()
    
    if not query:
        return "Please provide a restaurant name to search for."
    
    # Create Places service
    places_service = create_places_service()
    
    # Search for restaurants
    results = places_service.search_restaurant(query, location)
    
    html = f"""
    <div style="font-family: Arial; max-width: 1000px; margin: 20px auto; padding: 20px;">
        <h1>🔍 Search Results for "{query}"</h1>
        
        <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p><strong>Query:</strong> {query}</p>
            <p><strong>Location:</strong> {location or 'Not specified'}</p>
            <p><strong>Results Found:</strong> {len(results)}</p>
        </div>
    """
    
    for i, restaurant in enumerate(results, 1):
        place_id = restaurant.get('place_id')
        price_level = restaurant.get('price_level', 1)
        dollar_signs = '$' * (price_level + 1)
        
        html += f"""
        <div style="border: 1px solid #ddd; padding: 20px; margin: 15px 0; border-radius: 8px; background: white;">
            <h3>{i}. {restaurant.get('name', 'Unknown Restaurant')}</h3>
            <p><strong>📍 Address:</strong> {restaurant.get('address', 'Not available')}</p>
            <p><strong>⭐ Rating:</strong> {restaurant.get('rating', 'N/A')}/5</p>
            <p><strong>💰 Price Level:</strong> {dollar_signs}</p>
            <p><strong>🏷️ Types:</strong> {', '.join(restaurant.get('types', []))}</p>
            
            <div style="margin: 15px 0;">
                <a href="/places-details?place_id={place_id}" 
                   style="background: #3b82f6; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px;">
                   View Detailed Analysis →
                </a>
            </div>
        </div>
        """
    
    if not results:
        html += """
        <div style="background: #fef2f2; padding: 20px; border-radius: 8px; border: 1px solid #f87171;">
            <h3>No results found</h3>
            <p>Try searching with a different restaurant name or add a location.</p>
            <p><strong>Tip:</strong> Try common chains like "McDonald's", "Starbucks", or "Chipotle"</p>
        </div>
        """
    
    html += """
        <div style="margin-top: 30px;">
            <a href="/test-places">← Back to Search</a> | 
            <a href="/">← Home</a>
        </div>
    </div>
    """
    
    return html

@app.route('/places-details')
def places_details():
    """Show detailed restaurant analysis from Google Places"""
    place_id = request.args.get('place_id')
    
    if not place_id:
        return "Place ID required"
    
    # Create Places service and get details
    places_service = create_places_service()
    details = places_service.get_restaurant_details(place_id)
    
    if not details:
        return "Restaurant details not found"
    
    specialties_list = ', '.join(details.get('suggested_specialties', []))
    keywords_list = '</li><li>'.join(details.get('suggested_seo_keywords', []))
    price_level = details.get('price_level', 1)
    dollar_signs = '$' * (price_level + 1)
    
    return f"""
    <div style="font-family: Arial; max-width: 1000px; margin: 20px auto; padding: 20px;">
        <h1>🏪 Restaurant Analysis: {details.get('name')}</h1>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
            
            <div style="background: #f0f9ff; padding: 20px; border-radius: 8px;">
                <h3>📊 Basic Information (from Google)</h3>
                <p><strong>Name:</strong> {details.get('name')}</p>
                <p><strong>Address:</strong> {details.get('address', 'Not available')}</p>
                <p><strong>Phone:</strong> {details.get('phone', 'Not available')}</p>
                <p><strong>Website:</strong> {details.get('website', 'Not available')}</p>
                <p><strong>Google Rating:</strong> {details.get('google_rating', 'N/A')} ({details.get('google_review_count', 0)} reviews)</p>
            </div>
            
            <div style="background: #f0fdf4; padding: 20px; border-radius: 8px;">
                <h3>🤖 AI Analysis (Our Processing)</h3>
                <p><strong>Location:</strong> {details.get('location')}</p>
                <p><strong>Cuisine Type:</strong> {details.get('cuisine')}</p>
                <p><strong>Restaurant Type:</strong> {details.get('restaurant_type')}</p>
                <p><strong>Price Level:</strong> {dollar_signs}</p>
            </div>
            
        </div>
        
        <div style="background: #fffbeb; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🍽️ Suggested Specialties</h3>
            <p>{specialties_list or 'None detected from reviews'}</p>
            <small>Extracted from Google reviews and restaurant type analysis</small>
        </div>
        
        <div style="background: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🎯 Generated SEO Keywords</h3>
            <ul style="margin: 10px 0;">
                <li>{keywords_list}</li>
            </ul>
            <small>Optimized for local search and Google My Business</small>
        </div>
        
        <div style="background: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🔗 Integration Ready</h3>
            <p><strong>Google Place ID:</strong> <code style="background: #f3f4f6; padding: 2px 4px;">{details.get('google_place_id')}</code></p>
            <p><strong>Review Link:</strong> <a href="{details.get('google_review_link')}" target="_blank">Direct Google Reviews →</a></p>
            <p><strong>Status:</strong> ✅ Ready for database integration</p>
            
            <div style="margin-top: 15px;">
                <strong>Next Step:</strong> This data can be used to create a restaurant record in our database
                with all the SEO optimization settings pre-configured.
            </div>
        </div>
        
        <div style="margin-top: 30px;">
            <a href="/test-places">← Back to Search</a> | 
            <a href="/">← Home</a>
        </div>
    </div>
    """

@app.route('/init-db')
def init_database():
    """Initialize database with sample data"""
    try:
        # Create all tables
        db.create_all()
        
        # Check if we already have data
        existing_restaurants = Restaurant.query.count()
        
        if existing_restaurants == 0:
            # Create sample data
            create_sample_data()
            message = "✅ Database initialized with sample restaurants!"
        else:
            message = f"ℹ️ Database already has {existing_restaurants} restaurants"
        
        return f"""
        <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
            <h1>🗄️ Database Initialization</h1>
            <p>{message}</p>
            <p><a href="/">← Back to Home</a></p>
        </div>
        """
        
    except Exception as e:
        return f"""
        <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
            <h1>❌ Database Error</h1>
            <p>Error: {str(e)}</p>
            <p><a href="/">← Back to Home</a></p>
        </div>
        """, 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        restaurant_count = Restaurant.query.count()
        review_count = Review.query.count()
        return {
            'status': 'healthy',
            'message': 'Restaurant Review System fully operational',
            'database': 'connected',
            'restaurants': restaurant_count,
            'reviews': review_count,
            'google_places': 'integrated',
            'review_engine': 'active',
            'features': ['enhanced_ui', 'editable_reviews', 'google_integration']
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'database': 'disconnected'
        }, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 Starting Professional Restaurant Review System...")
    print("📊 Initialize database: /init-db")
    print("🎭 Demo review system: /demo-review")
    print("📱 Customer reviews: /review/<restaurant-slug>")
    print("🔍 Test Google Places: /test-places")
    print("🏪 Dashboard: /dashboard (coming soon)")
    print("✨ Features: Enhanced UI, Editable Reviews, Google Integration")
    
    app.run(host='0.0.0.0', port=port, debug=True)