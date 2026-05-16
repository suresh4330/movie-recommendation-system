"""
Test script to verify the API module imports successfully.
"""

import sys

sys.path.insert(0, ".")

from main import app
from ml_models import HybridRecommender


assert app is not None
assert HybridRecommender is not None

print("All imports successful.")
print("FastAPI app initialized.")
print("Ready to start server with: uvicorn main:app --reload")
