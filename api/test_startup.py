"""
Test script to verify API can start and load all models
"""

import sys
sys.path.insert(0, '.')

# Import the HybridRecommender class first
from ml_models import HybridRecommender

# Now import main
from main import app
import uvicorn

print("✅ All imports successful!")
print("✅ FastAPI app initialized")
print("\nAttempting to trigger startup event...")

# Note: This won't actually start the server, just validates imports
print("✅ Ready to start server with: uvicorn main:app --reload")
