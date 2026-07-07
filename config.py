import os

class Config:
    # Flask app secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'premium-glassmorphic-secret-key-9982'
    
    # Base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Database Configuration (SQLite default fallback, toggle to MySQL easily)
    # To use MySQL: mysql+pymysql://username:password@localhost/db_name
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'attendance.db')
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Configurations
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    PROFILE_FOLDER = os.path.join(UPLOAD_FOLDER, 'profile_pics')
    DATASET_FOLDER = os.path.join(UPLOAD_FOLDER, 'face_dataset')
    
    @staticmethod
    def ensure_upload_dirs():
        os.makedirs(Config.PROFILE_FOLDER, exist_ok=True)
        os.makedirs(Config.DATASET_FOLDER, exist_ok=True)
    
    # Max file size: 16MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
