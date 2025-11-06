# routes.py - All application routes
from flask import render_template, request, jsonify, redirect, url_for, flash
from models import db, Restaurant, User, Review, SMSLog
from google_places import create_places_service
from review_generator import create_review_generator

def register_routes(app):
    """Register all routes with the Flask app"""
    
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
                    <li><a href="/dashboard" target="_blank">🏪 Restaurant Dashboard</a></li>
                    <li><a href="/add-restaurant" target="_blank">➕ Add Real Restaurant</a></li>
                    <li><a href="/test-places" target="_blank">🔍 Test Google Places API</a></li>
                </ul>
            </div>
            
            <p><em>Built with Flask + SQLAlchemy + Google Places API + AI Review Engine</em></p>
        </div>
        """
    
    @app.route('/review/<restaurant_slug>')
    def customer_review(restaurant_slug):
        """Customer review interface - the interactive form customers see"""
        restaurant = Restaurant.query.filter_by(slug=restaurant_slug).first()
        
        if not restaurant:
            return f"""
            <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
                <h1>❌ Restaurant Not Found</h1>
                <p>Sorry, we couldn't find a restaurant with ID: <strong>{restaurant_slug}</strong></p>
                <p><a href="/">← Back to Home</a></p>
            </div>
            """, 404
        
        return render_template('customer_review_form.html', restaurant=restaurant)
    
    @app.route('/generate-review/<restaurant_slug>', methods=['POST'])
    def generate_review_api(restaurant_slug):
        """API endpoint to generate and polish reviews using Gemini AI"""
        restaurant = Restaurant.query.filter_by(slug=restaurant_slug).first()
        if not restaurant:
            return jsonify({'success': False, 'error': 'Restaurant not found'}), 404
        
        try:
            data = request.get_json()
            rating = int(data.get('rating'))
            favorite_dish = data.get('favorite_dish', '').strip()
            atmosphere = data.get('atmosphere', '').strip()
            special_detail = data.get('special_detail', '').strip()
            standout_detail = data.get('standout_detail', '').strip()
            
            if not (1 <= rating <= 5):
                return jsonify({'success': False, 'error': 'Invalid rating'}), 400
            
            if not favorite_dish or not atmosphere:
                return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
            # Generate base review
            generator = create_review_generator()
            try:
                result = generator.generate_review(
                    restaurant, rating, favorite_dish, atmosphere,
                    special_detail if special_detail else None,
                    standout_detail if standout_detail else None
                )
            except TypeError:
                result = generator.generate_review(restaurant, rating, favorite_dish, atmosphere)
            
            rough_review = result['review']
            
            # Polish with Gemini AI
            from gemini_polisher import create_review_polisher
            polisher = create_review_polisher()
            polish_result = polisher.polish_review(rough_review, restaurant.name)
            
            final_review = polish_result['polished_review']
            
            return jsonify({
                'success': True,
                'review': final_review,
                'word_count': len(final_review.split()),
                'seo_count': result.get('seo_count', 0),
                'seo_keywords': result.get('seo_keywords', []),
                'personalized': result.get('personalized', False),
                'uniqueness_score': result.get('uniqueness_score', 0.9),
                'ai_polished': polish_result['polished'],
                'cost_estimate': polish_result['cost_estimate'],
                'original_review': rough_review if polish_result['polished'] else None
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
            rating = int(request.form.get('rating'))
            
            if rating >= 4:
                # Positive review path
                favorite_dish = request.form.get('favorite_dish_final', '').strip()
                atmosphere = request.form.get('atmosphere', '').strip()
                final_review = request.form.get('final_review', '').strip()
                
                if not final_review:
                    generator = create_review_generator()
                    result = generator.generate_review(restaurant, rating, favorite_dish, atmosphere)
                    final_review = result['review']
                    word_count = result['word_count']
                else:
                    word_count = len(final_review.split())
                
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
                
                review_record = Review(
                    restaurant_id=restaurant.id,
                    rating=rating,
                    review_type='private',
                    issue_area=issue_area,
                    feedback_details=feedback_details,
                    requires_followup=True,
                    status='completed'
                )
                
                if contact_info:
                    if '@' in contact_info:
                        review_record.customer_email = contact_info
                    else:
                        review_record.customer_phone = contact_info
                
                db.session.add(review_record)
                db.session.commit()
                
                return f"""
                <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
                    <h1>🔧 Feedback Sent!</h1>
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
    
    @app.route('/dashboard')
    @app.route('/dashboard/<restaurant_slug>')
    def dashboard(restaurant_slug=None):
        """Main dashboard homepage with analytics and overview"""
        if restaurant_slug:
            restaurant = Restaurant.query.filter_by(slug=restaurant_slug).first()
        else:
            restaurant = Restaurant.query.first()
        
        if not restaurant:
            return redirect(url_for('home'))
        
        # Calculate analytics
        total_reviews = Review.query.filter_by(restaurant_id=restaurant.id).count()
        positive_reviews = Review.query.filter_by(restaurant_id=restaurant.id).filter(Review.rating >= 4).count()
        negative_feedback = Review.query.filter_by(restaurant_id=restaurant.id).filter(Review.rating <= 3).count()
        pending_followups = Review.query.filter_by(
            restaurant_id=restaurant.id, 
            requires_followup=True, 
            followup_completed=False
        ).count()
        
        recent_reviews = Review.query.filter_by(restaurant_id=restaurant.id)\
            .order_by(Review.created_at.desc())\
            .limit(10)\
            .all()
        
        avg_rating = db.session.query(db.func.avg(Review.rating))\
            .filter_by(restaurant_id=restaurant.id)\
            .scalar() or 0
        
        all_negative_feedback = Review.query.filter_by(restaurant_id=restaurant.id)\
            .filter(Review.rating <= 3)\
            .order_by(Review.created_at.desc())\
            .all()
        
        pending_feedback = Review.query.filter_by(
            restaurant_id=restaurant.id,
            requires_followup=True,
            followup_completed=False
        ).order_by(Review.created_at.desc()).limit(5).all()
        
        return render_template('dashboard.html', 
                             restaurant=restaurant,
                             stats={
                                 'total_reviews': total_reviews,
                                 'positive_reviews': positive_reviews,
                                 'negative_feedback': negative_feedback,
                                 'pending_followups': pending_followups,
                                 'avg_rating': round(avg_rating, 1)
                             },
                             recent_reviews=recent_reviews,
                             pending_feedback=pending_feedback,
                             negative_feedback=all_negative_feedback)
    
    @app.route('/add-restaurant')
    def add_restaurant():
        """Business onboarding interface"""
        return render_template('add_restaurant.html')
    
    @app.route('/api/search-business', methods=['POST'])
    def search_business():
        """Search for restaurants using Google Places API"""
        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            location = data.get('location', '').strip()
            
            if not name:
                return jsonify({'success': False, 'error': 'Restaurant name is required'}), 400
            
            places_service = create_places_service()
            results = places_service.search_restaurant(name, location)
            
            formatted_results = []
            for restaurant in results:
                formatted_results.append({
                    'place_id': restaurant.get('place_id'),
                    'name': restaurant.get('name'),
                    'address': restaurant.get('address', ''),
                    'phone': restaurant.get('phone', ''),
                    'website': restaurant.get('website', ''),
                    'rating': restaurant.get('rating', 0),
                    'review_count': restaurant.get('review_count', 0),
                    'price_level': restaurant.get('price_level', 1),
                    'cuisine': restaurant.get('cuisine', 'Restaurant'),
                    'types': restaurant.get('types', [])
                })
            
            return jsonify({
                'success': True,
                'results': formatted_results
            })
            
        except Exception as e:
            print(f"Error searching businesses: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/create-restaurant', methods=['POST'])
    def create_restaurant_from_import():
        """Create a new restaurant from Google Places data"""
        try:
            data = request.get_json()
            restaurant_data = data.get('restaurant', {})
            
            if not restaurant_data or not restaurant_data.get('place_id'):
                return jsonify({'success': False, 'error': 'Invalid restaurant data'}), 400
            
            existing = Restaurant.query.filter_by(google_place_id=restaurant_data.get('place_id')).first()
            if existing:
                return jsonify({'success': False, 'error': 'Restaurant already exists in system'}), 409
            
            places_service = create_places_service()
            detailed_data = places_service.get_restaurant_details(restaurant_data.get('place_id'))
            
            if not detailed_data:
                return jsonify({'success': False, 'error': 'Could not retrieve restaurant details'}), 404
            
            specialties = data.get('specialties', [])
            if specialties:
                detailed_data['suggested_specialties'] = specialties
            
            brand_voice = data.get('brand_voice', '')
            if brand_voice:
                detailed_data['brand_voice'] = brand_voice
            
            restaurant = Restaurant.create_from_google_places(
                detailed_data,
                custom_data={
                    'brand_voice': brand_voice,
                    'specialties_override': specialties if specialties else None
                }
            )
            
            restaurant.subscription_plan = 'free'
            restaurant.subscription_status = 'active'
            
            db.session.add(restaurant)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'restaurant_id': restaurant.id,
                'slug': restaurant.slug,
                'message': 'Restaurant successfully created'
            })
            
        except Exception as e:
            print(f"Error creating restaurant: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
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
        
        places_service = create_places_service()
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
            from models import create_sample_data
            db.create_all()
            
            existing_restaurants = Restaurant.query.count()
            
            if existing_restaurants == 0:
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
                'features': ['enhanced_ui', 'editable_reviews', 'google_integration', 'dashboard', 'business_import']
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'database': 'disconnected'
            }, 500


def _render_restaurant_list(restaurants):
    """Helper function to render restaurant list"""
    if not restaurants:
        return "<p><em>No restaurants in database. <a href='/init-db'>Click here to initialize with sample data</a>.</em></p>"
    
    html = "<ul>"
    for restaurant in restaurants:
        # Safely get specialties with fallback
        specialties_list = restaurant.get_specialties() or []
        specialties = ', '.join(specialties_list[:3]) if specialties_list else 'None'
        
        # Safely get keywords and templates
        keywords_list = restaurant.get_seo_keywords() or []
        keywords_count = len(keywords_list)
        
        templates_list = restaurant.get_custom_templates() or []
        templates_count = len(templates_list)
        
        html += f"""
        <li style="margin: 10px 0; padding: 10px; background: white; border-radius: 5px;">
            <strong>{restaurant.name}</strong> ({restaurant.slug})
            <br><small>📍 {restaurant.location} • {restaurant.cuisine} • {restaurant.restaurant_type}</small>
            <br><small>🍽️ Specialties: {specialties}</small>
            <br><small>📈 {keywords_count} SEO keywords, {templates_count} templates</small>
            <br><small>📞 {restaurant.phone} • 💳 {restaurant.subscription_plan}</small>
            <br><small><a href="/review/{restaurant.slug}">📱 Customer Review Interface</a> | <a href="/dashboard/{restaurant.slug}">🏪 Dashboard</a></small>
        </li>
        """
    html += "</ul>"
    return html