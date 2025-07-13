#!/usr/bin/env python3
"""
Integration test script to verify the reorganized structure works
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test core modules
        from src.core.database import DatabaseConnection
        from src.core.sheets import GoogleSheetsConnection
        print("✓ Core modules imported successfully")
        
        # Test sync modules  
        from src.sync.continuous_sync import NeonToSheetsSync
        from src.sync.one_time_sync import OneTimeSyncToSheets
        print("✓ Sync modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_environment():
    """Test that environment variables are loaded"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['PGHOST', 'PGDATABASE', 'TABLE_NAME']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"✗ Missing environment variables: {missing}")
        return False
    else:
        print("✓ Required environment variables found")
        return True

def test_database_connection():
    """Test database connection"""
    try:
        from src.core.database import DatabaseConnection
        db = DatabaseConnection()
        
        if db.connect():
            print("✓ Database connection successful")
            db.disconnect()
            return True
        else:
            print("✗ Database connection failed")
            return False
            
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Neon to Google Sheets - Integration Test")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Environment Variables", test_environment), 
        ("Database Connection", test_database_connection)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        
    print("\n" + "=" * 50)
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed! The reorganized structure is working correctly.")
        return True
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
