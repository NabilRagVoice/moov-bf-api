from flask import Flask
from flask_cors import CORS
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    
    # Register blueprints
    from app.routes.health import health_bp
    from app.routes.accords_haut_debit import accords_hd_bp
    from app.routes.accords_mobile import accords_mobile_bp
    from app.routes.accords_moov_money import accords_mm_bp
    from app.routes.offres import offres_bp
    from app.routes.admin import admin_bp
    from app.routes.config_routes import config_bp
    
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(accords_hd_bp, url_prefix='/api/accords/haut-debit')
    app.register_blueprint(accords_mobile_bp, url_prefix='/api/accords/mobile')
    app.register_blueprint(accords_mm_bp, url_prefix='/api/accords/moov-money')
    app.register_blueprint(offres_bp, url_prefix='/api/offres')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    
    return app
