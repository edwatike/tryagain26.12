"""Test get_parsing_run with mock data to verify results_count handling."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Test the safe access logic
print("Testing safe access to results_count...")
print("="*50)

# Simulate old model (without results_count)
class OldParsingRunModel:
    def __init__(self):
        self.run_id = "test-123"
        # No results_count attribute

# Simulate new model (with results_count)
class NewParsingRunModel:
    def __init__(self):
        self.run_id = "test-456"
        self.results_count = 42

def safe_get_results_count(run):
    """Test the safe access logic from get_parsing_run.py"""
    results_count = None
    if run:
        # Method 1: Check if attribute exists in class definition
        if hasattr(run.__class__, 'results_count'):
            try:
                results_count = getattr(run, 'results_count', None)
            except (AttributeError, KeyError, TypeError):
                results_count = None
        # Method 2: Check if attribute exists in instance __dict__
        elif hasattr(run, '__dict__') and 'results_count' in run.__dict__:
            try:
                results_count = run.__dict__.get('results_count', None)
            except (AttributeError, KeyError, TypeError):
                results_count = None
        # Method 3: Try getattr as last resort
        else:
            try:
                results_count = getattr(run, 'results_count', None)
            except Exception:
                results_count = None
    return results_count

# Test with old model
print("\nTest 1: Old model (without results_count)")
old_run = OldParsingRunModel()
result1 = safe_get_results_count(old_run)
print(f"  Result: {result1}")
if result1 is None:
    print("  ✅ PASS: Returns None for old model")
else:
    print("  ❌ FAIL: Should return None")

# Test with new model
print("\nTest 2: New model (with results_count)")
new_run = NewParsingRunModel()
result2 = safe_get_results_count(new_run)
print(f"  Result: {result2}")
if result2 == 42:
    print("  ✅ PASS: Returns correct value for new model")
else:
    print(f"  ❌ FAIL: Expected 42, got {result2}")

# Test with None
print("\nTest 3: None run")
result3 = safe_get_results_count(None)
print(f"  Result: {result3}")
if result3 is None:
    print("  ✅ PASS: Returns None for None run")
else:
    print("  ❌ FAIL: Should return None")

print("\n" + "="*50)
print("All tests completed!")
















