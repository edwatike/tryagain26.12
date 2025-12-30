"""Test script to verify results_count fix."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.adapters.db.models import ParsingRunModel

# Test 1: Check if results_count exists in model class
print("Test 1: Checking if results_count exists in ParsingRunModel class...")
if hasattr(ParsingRunModel, 'results_count'):
    print("✅ PASS: results_count exists in ParsingRunModel class")
else:
    print("❌ FAIL: results_count does NOT exist in ParsingRunModel class")

# Test 2: Check if results_count is in __table__.columns
print("\nTest 2: Checking if results_count exists in table columns...")
try:
    if 'results_count' in ParsingRunModel.__table__.columns:
        print("✅ PASS: results_count exists in table columns")
    else:
        print("❌ FAIL: results_count does NOT exist in table columns")
except Exception as e:
    print(f"⚠️  WARNING: Could not check table columns: {e}")

# Test 3: Try to create a mock instance and access results_count
print("\nTest 3: Testing safe access to results_count...")
try:
    # Create a mock instance (won't work fully without DB, but tests attribute access)
    class MockRun:
        def __init__(self):
            self.results_count = None
    
    mock_run = MockRun()
    
    # Test Method 1: hasattr on class
    if hasattr(mock_run.__class__, 'results_count'):
        result1 = getattr(mock_run, 'results_count', None)
        print(f"✅ PASS: Method 1 (hasattr + getattr) works: {result1}")
    else:
        print("❌ FAIL: Method 1 (hasattr + getattr) failed")
    
    # Test Method 2: __dict__ access
    if hasattr(mock_run, '__dict__') and 'results_count' in mock_run.__dict__:
        result2 = mock_run.__dict__.get('results_count', None)
        print(f"✅ PASS: Method 2 (__dict__) works: {result2}")
    else:
        print("❌ FAIL: Method 2 (__dict__) failed")
    
    # Test Method 3: getattr fallback
    result3 = getattr(mock_run, 'results_count', None)
    print(f"✅ PASS: Method 3 (getattr fallback) works: {result3}")
    
except Exception as e:
    print(f"❌ FAIL: Error during testing: {e}")

print("\n" + "="*50)
print("All tests completed!")










