"""Configuration management for the PDF Accessibility Compliance Engine"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = FLASK_ENV == 'development'
    
    # Logging Configuration
    ENABLE_API_LOGGING = os.getenv('ENABLE_API_LOGGING', 'true').lower() == 'true'
    ENABLE_VERBOSE_LOGGING = os.getenv('ENABLE_VERBOSE_LOGGING', 'false').lower() == 'true'
    
    # API Configuration
    API_VERSION = 'v1'
    API_PREFIX = f'/api/{API_VERSION}'
    API_V2_PREFIX = '/api/v2'
    
    # PDF Processing Configuration
    MAX_FILE_SIZE_MB = 50
    SUPPORTED_LOCATOR_SCHEMES = ['http', 'https', 'file']
    MAX_MEMORY_MB = int(os.getenv('MAX_MEMORY_MB', '100'))
    EPHEMERAL_MODE = os.getenv('EPHEMERAL_MODE', 'true').lower() == 'true'
    ENABLE_PII_DETECTION = os.getenv('ENABLE_PII_DETECTION', 'true').lower() == 'true'
    
    # Gemini Model Configuration
    GEMINI_MODEL = 'gemini-2.5-flash'
    GEMINI_TEMPERATURE = 0.7
    GEMINI_MAX_TOKENS = 2048
    GEMINI_TIMEOUT = 30
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY:
            print("WARNING: GEMINI_API_KEY not set. LLM features will use fallback responses.")
        return True


# Validate configuration on import
Config.validate()
