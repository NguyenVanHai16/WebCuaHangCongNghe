from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
import logging

# Thiết lập logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Khởi tạo SQLAlchemy
db = SQLAlchemy()

# Khởi tạo Flask-Migrate
migrate = Migrate()

def create_app():
    app = Flask(__name__, template_folder='templates')

    # Cấu hình ứng dụng
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'techmart-default-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:12345@localhost/techmart?charset=utf8mb4'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'app/static/uploads/sanpham')

    # Khởi tạo cơ sở dữ liệu
    try:
        db.init_app(app)
        logger.debug("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

    # Khởi tạo Migrate với app và db
    migrate.init_app(app, db)

    # Đăng ký các blueprint
    try:
        from app.admin.routes import admin_bp
        from app.auth.routes import auth
        from app.main.routes import main
        from app.products.routes import products
        from app.cart.routes import cart
        from app.orders.routes import orders_bp

        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(auth)
        app.register_blueprint(main)
        app.register_blueprint(products)
        app.register_blueprint(cart)
        app.register_blueprint(orders_bp)
        logger.debug("Blueprints registered successfully")

        # Kiểm tra các route trong blueprint products
        with app.app_context():
            product_routes = [str(rule) for rule in app.url_map.iter_rules() if rule.endpoint.startswith('products.')]
            logger.debug(f"Registered product routes: {product_routes}")
            if any('/like_product/<int:product_id>' in route for route in product_routes):
                logger.debug("Endpoint /like_product/<int:product_id> registered successfully")
            else:
                logger.error("Endpoint /like_product/<int:product_id> NOT registered")
    except Exception as e:
        logger.error(f"Failed to register blueprints: {str(e)}")
        raise

    # Thiết lập flask-login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để sử dụng chức năng này.'
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        user = User.query.get(int(user_id))
        logger.debug(f"Loading user {user_id}: {'Found' if user else 'Not found'}")
        return user

    # Tạo tất cả các bảng trong cơ sở dữ liệu
    with app.app_context():
        try:
            db.create_all()
            logger.debug("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise

    return app