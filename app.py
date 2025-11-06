# app.py - Main application setup
from flask import Flask
from models import db
from flask_login import login_user, logout_user, login_required
import os

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///restaurant_reviews.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Register routes
    from routes import register_routes
    register_routes(app)
    
    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    print("Starting Restaurant Review System...")
    print("Initialize database: /init-db")
    print("Customer reviews: /review/<restaurant-slug>")
    print("Restaurant dashboard: /dashboard")
    
    app.run(host='0.0.0.0', port=port, debug=True)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Handle new user registration
    pass

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Handle user login
    pass