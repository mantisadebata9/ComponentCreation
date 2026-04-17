# Configuration file for the backend

import os

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Debug mode
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Other configurations
# Add more configurations as necessary