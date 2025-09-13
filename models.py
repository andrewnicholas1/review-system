# models.py - Database Models for Restaurant Review System
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json
import re

# Initialize SQLAlchemy (database interface)
db = SQLAlchemy()

class Restaurant(db.Model):
    """
    Restaurant model - HYBRID approach
    Combines Google Places data with custom review settings
    """
    __tablename__ = 'restaurants'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # === GOOGLE PLACES DATA (Auto-populated) ===
    google_place_id = db.Column(db.String(200), unique=True)  # Primary Google identifier
    
    # Basic info from Google (auto-synced)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)  # URL-friendly name
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    website = db.Column(db.String(500))
    google_rating = db.Column(db.Float)  # Current Google rating
    google_review_count = db.Column(db.Integer)  # Number of Google reviews
    google_review_link = db.Column(db.String(500))
    
    # Location and categorization
    location = db.Column(db.String(200), nullable=False)  # City/neighborhood
    cuisine = db.Column(db.String(100), nullable=False)  # Mexican, Italian, etc.
    restaurant_type = db.Column(db.String(50), default='casual')  # casual, upscale, fast_casual
    
    # === CUSTOM REVIEW OPTIMIZATION DATA (User-defined) ===
    # Review optimization settings (what makes us valuable)
    specialties = db.Column(db.Text)  # JSON - dishes to highlight in reviews
    seo_keywords = db.Column(db.Text)  # JSON - local SEO terms
    custom_templates = db.Column(db.Text)  # JSON - branded review templates
    brand_voice = db.Column(db.Text)  # How they want to sound
    
    # === SYNC STATUS ===
    google_last_synced = db.Column(db.DateTime)
    google_sync_enabled = db.Column(db.Boolean, default=True)
    
    # === SUBSCRIPTION & SETTINGS ===
    subscription_plan = db.Column(db.String(20), default='free')  # free, pro, enterprise
    subscription_status = db.Column(db.String(20), default='active')
    stripe_customer_id = db.Column(db.String(100))
    
    # Contact info
    email = db.Column(db.String(200))
    
    # Auto-SMS settings
    auto_sms_enabled = db.Column(db.Boolean, default=False)
    sms_delay_hours = db.Column(db.Integer, default=2)  # Hours after dining
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='restaurant', lazy=True)
    reviews = db.relationship('Review', backref='restaurant', lazy=True)
    
    def __init__(self, **kwargs):
        super(Restaurant, self).__init__(**kwargs)
        # Set default values for JSON fields
        if not self.specialties:
            self.specialties = json.dumps([])
        if not self.seo_keywords:
            self.seo_keywords = json.dumps([])
        if not self.custom_templates:
            self.custom_templates = json.dumps([])
    
    def get_specialties(self):
        """Get specialties as Python list"""
        try:
            return json.loads(self.specialties or '[]')
        except:
            return []
    
    def set_specialties(self, specialties_list):
        """Set specialties from Python list"""
        self.specialties = json.dumps(specialties_list)
    
    def get_seo_keywords(self):
        """Get SEO keywords as Python list"""
        try:
            return json.loads(self.seo_keywords or '[]')
        except:
            return []
    
    def set_seo_keywords(self, keywords_list):
        """Set SEO keywords from Python list"""
        self.seo_keywords = json.dumps(keywords_list)
    
    def get_custom_templates(self):
        """Get templates as Python list"""
        try:
            return json.loads(self.custom_templates or '[]')
        except:
            return []
    
    def set_custom_templates(self, templates_list):
        """Set templates from Python list"""
        self.custom_templates = json.dumps(templates_list)
    
    @classmethod
    def create_from_google_places(cls, places_data: dict, custom_data: dict = None):
        """
        Factory method to create Restaurant from Google Places data
        Combines Google's data with user customizations
        """
        # Generate URL-friendly slug from name
        slug = re.sub(r'[^\w\s-]', '', places_data['name'].lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        
        # Create restaurant instance
        restaurant = cls(
            # Google Places data
            google_place_id=places_data.get('google_place_id'),
            name=places_data.get('name'),
            address=places_data.get('address'),
            phone=places_data.get('phone'),
            website=places_data.get('website'),
            google_rating=places_data.get('google_rating', 0),
            google_review_count=places_data.get('google_review_count', 0),
            google_review_link=places_data.get('google_review_link'),
            
            # Processed data
            slug=slug,
            cuisine=places_data.get('cuisine', 'Restaurant'),
            location=places_data.get('location', 'Local Area'),
            restaurant_type=places_data.get('restaurant_type', 'casual'),
            
            # Sync status
            google_last_synced=datetime.utcnow(),
            google_sync_enabled=True,
            
            # Default subscription
            subscription_plan='free',
            subscription_status='active'
        )
        
        # Set Google-suggested data
        restaurant.set_specialties(places_data.get('suggested_specialties', []))
        restaurant.set_seo_keywords(places_data.get('suggested_seo_keywords', []))
        
        # Apply any custom user data
        if custom_data:
            if 'brand_voice' in custom_data:
                restaurant.brand_voice = custom_data['brand_voice']
            if 'custom_templates' in custom_data:
                restaurant.set_custom_templates(custom_data['custom_templates'])
            if 'specialties_override' in custom_data:
                restaurant.set_specialties(custom_data['specialties_override'])
        
        return restaurant
    
    def __repr__(self):
        return f'<Restaurant {self.name}>'

class User(UserMixin, db.Model):
    """
    User model - restaurant owners/managers who log into the dashboard
    Uses Flask-Login for authentication
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User info
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    
    # Role and permissions
    role = db.Column(db.String(20), default='owner')  # owner, manager, staff
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Foreign key to restaurant
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.email}>'

class Review(db.Model):
    """
    Review model - stores all customer feedback (both public and private)
    This is the core of our analytics and reporting
    """
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Review basics
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review_type = db.Column(db.String(20), nullable=False)  # 'public' or 'private'
    
    # Customer info (optional)
    customer_phone = db.Column(db.String(20))
    customer_email = db.Column(db.String(200))
    customer_name = db.Column(db.String(200))
    
    # Review content
    favorite_dish = db.Column(db.String(200))
    atmosphere = db.Column(db.String(200))
    generated_review = db.Column(db.Text)  # The final review text
    word_count = db.Column(db.Integer)
    
    # For negative feedback
    issue_area = db.Column(db.String(200))  # food, service, cleanliness, etc.
    feedback_details = db.Column(db.Text)
    requires_followup = db.Column(db.Boolean, default=False)
    followup_completed = db.Column(db.Boolean, default=False)
    
    # Tracking
    source = db.Column(db.String(50), default='sms')  # sms, email, qr, manual
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Status
    status = db.Column(db.String(20), default='completed')  # pending, completed, posted
    posted_to_google = db.Column(db.Boolean, default=False)
    google_review_id = db.Column(db.String(200))
    
    # Foreign key
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_positive(self):
        """Check if this is a positive review (4-5 stars)"""
        return self.rating >= 4
    
    def is_negative(self):
        """Check if this is negative feedback (1-3 stars)"""
        return self.rating <= 3
    
    def get_rating_stars(self):
        """Return rating as star emojis"""
        return '⭐' * self.rating
    
    def __repr__(self):
        return f'<Review {self.rating}★ for {self.restaurant.name}>'

class SMSLog(db.Model):
    """
    SMS Log - tracks all SMS messages sent to customers
    Important for analytics and avoiding spam
    """
    __tablename__ = 'sms_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # SMS details
    to_phone = db.Column(db.String(20), nullable=False)
    message_body = db.Column(db.Text, nullable=False)
    twilio_sid = db.Column(db.String(100))  # Twilio message ID
    
    # Status tracking
    status = db.Column(db.String(20), default='sent')  # sent, delivered, failed
    error_message = db.Column(db.Text)
    
    # Foreign key
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    
    # Timestamps
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SMS to {self.to_phone}>'

# Helper function to initialize database
def create_sample_data():
    """
    Create sample restaurants for testing
    This will run when we first set up the database
    """
    
    # Sample Restaurant 1: Pablo's Mexican
    pablos = Restaurant(
        name="Pablo's Authentic Mexican Cantina",
        slug="pablos-mexican",
        cuisine="Mexican",
        location="downtown Seattle",
        restaurant_type="casual",
        phone="+1-206-555-0123",
        email="info@pablos.com",
        address="123 Pike Street, Seattle, WA 98101",
        google_review_link="https://search.google.com/local/writereview?placeid=ChIJpablos123",
        subscription_plan="pro",
        brand_voice="Fun, energetic, uses Spanish phrases and food emojis"
    )
    
    # Set up Pablo's specialties and keywords
    pablos.set_specialties(["tacos", "margaritas", "enchiladas", "guacamole", "burritos"])
    pablos.set_seo_keywords([
        "best Mexican restaurant downtown Seattle",
        "authentic tacos Seattle",
        "date night restaurant Seattle",
        "Mexican food near me",
        "fresh guacamole Seattle"
    ])
    pablos.set_custom_templates([
        "¡Increíble! Had a {rating}-star fiesta at {name}! The {dish} was absolutely amazing - {cuisine_praise}. Perfect spot for {atmosphere} and definitely {seo_keyword_1}. The {location} location is so convenient! {closing_praise}",
        "Taco Tuesday just got better! {name} serves incredible {rating}-star {cuisine} food. The {dish} was spectacular - {cuisine_praise}. Great for {atmosphere}, and honestly one of the {seo_keyword_1} around! {closing_praise}"
    ])
    
    # Sample Restaurant 2: Sophia's Italian
    sophias = Restaurant(
        name="Sophia's Fine Italian Dining",
        slug="sophias-italian",
        cuisine="Italian",
        location="Capitol Hill",
        restaurant_type="upscale",
        phone="+1-206-555-0456",
        email="manager@sophias.com",
        address="456 Broadway Ave, Seattle, WA 98102",
        google_review_link="https://search.google.com/local/writereview?placeid=ChIJsophias456",
        subscription_plan="enterprise",
        brand_voice="Elegant, sophisticated, wine-focused, traditional Italian"
    )
    
    sophias.set_specialties(["pasta", "risotto", "osso buco", "tiramisu", "wine"])
    sophias.set_seo_keywords([
        "fine dining Italian restaurant Seattle",
        "romantic dinner Capitol Hill",
        "best pasta Seattle",
        "Italian wine selection",
        "anniversary dinner restaurant"
    ])
    sophias.set_custom_templates([
        "Exceptional {rating}-star dining experience at {name}. The {dish} was expertly prepared - {cuisine_praise}. Perfect ambiance for {atmosphere}, truly {seo_keyword_1}. The {location} location adds to its charm. {closing_praise}"
    ])
    
    # Add to database
    db.session.add(pablos)
    db.session.add(sophias)
    db.session.commit()
    
    print("✅ Sample restaurants created!")
    return pablos, sophias