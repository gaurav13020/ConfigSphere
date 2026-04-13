import sys
import os

# Make delivery app importable for invalidation consumer tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "delivery"))
