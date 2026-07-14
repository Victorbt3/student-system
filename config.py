import os

class Config:
    # Flask app secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'premium-glassmorphic-secret-key-9982'
    
    # Supabase Configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    
    # Base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Vercel Environment Detection
    IS_VERCEL = os.environ.get('VERCEL') == '1'
    
    # Database Configuration
    if IS_VERCEL:
        default_db_path = 'sqlite:////tmp/attendance.db'
    else:
        default_db_path = 'sqlite:///' + os.path.join(BASE_DIR, 'attendance.db')
        
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or default_db_path

    # Debug: resolved DB URI (helps diagnose "data not saving")
    # Printed at import-time; safe for local/dev.
    print(f"[Config] SQLALCHEMY_DATABASE_URI={SQLALCHEMY_DATABASE_URI}")

        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Configurations
    if IS_VERCEL:
        UPLOAD_FOLDER = '/tmp/uploads'
    else:
        UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
        
    PROFILE_FOLDER = os.path.join(UPLOAD_FOLDER, 'profile_pics')
    DATASET_FOLDER = os.path.join(UPLOAD_FOLDER, 'face_dataset')
    
    @staticmethod
    def ensure_upload_dirs():
        os.makedirs(Config.PROFILE_FOLDER, exist_ok=True)
        os.makedirs(Config.DATASET_FOLDER, exist_ok=True)
    
    # Max file size: 16MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
