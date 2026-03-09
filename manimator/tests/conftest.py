import os
import sys

# Add backend to Python path so tests can import backend modules directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
