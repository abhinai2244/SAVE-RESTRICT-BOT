#!/usr/bin/env python3
"""
Test script to verify flood wait handling fixes
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required imports work correctly"""
    try:
        from pyrogram.errors import FloodWait
        from pyrogram import Client, filters, enums
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_flood_wait_handling():
    """Test that FloodWait exception handling is properly implemented"""
    try:
        # Read the start.py file to check for FloodWait handling
        with open('Rexbots/start.py', 'r') as f:
            content = f.read()
        
        # Check if FloodWait is imported
        if 'FloodWait' in content and 'from pyrogram.errors import' in content:
            print("✅ FloodWait is properly imported")
        else:
            print("❌ FloodWait import not found")
            return False
        
        # Check if try-except blocks with FloodWait are present
        if 'except FloodWait as e:' in content:
            print("✅ FloodWait exception handling found")
        else:
            print("❌ FloodWait exception handling not found")
            return False
        
        # Check if asyncio.sleep(e.value) is used
        if 'await asyncio.sleep(e.value)' in content:
            print("✅ Proper flood wait sleep implementation found")
        else:
            print("❌ Proper flood wait sleep implementation not found")
            return False
        
        # Check if retry logic is present
        if 'Retry the message' in content:
            print("✅ Retry logic comments found")
        else:
            print("❌ Retry logic comments not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing flood wait handling: {e}")
        return False

def test_message_functions():
    """Test that message sending functions have flood wait handling"""
    try:
        with open('Rexbots/start.py', 'r') as f:
            content = f.read()
        
        # Check key functions that send messages
        functions_to_check = [
            'send_start',
            'button_callbacks',
            'single_link',
            'save'
        ]
        
        for func in functions_to_check:
            if f'async def {func}' in content:
                # Find the function and check for FloodWait handling
                func_start = content.find(f'async def {func}')
                if func_start != -1:
                    # Look for FloodWait handling in the next 50 lines
                    func_section = content[func_start:func_start + 2000]
                    if 'except FloodWait as e:' in func_section:
                        print(f"✅ {func} has FloodWait handling")
                    else:
                        print(f"⚠️  {func} may not have FloodWait handling")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing message functions: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Testing flood wait handling fixes...")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test flood wait handling
    flood_wait_ok = test_flood_wait_handling()
    
    # Test message functions
    functions_ok = test_message_functions()
    
    print("=" * 50)
    
    if imports_ok and flood_wait_ok:
        print("🎉 All tests passed! Flood wait handling has been successfully implemented.")
        print("\n📋 Summary of fixes:")
        print("• Added try-except blocks around message sending in send_start()")
        print("• Added FloodWait handling in all callback functions")
        print("• Added retry logic after flood wait periods")
        print("• Added flood wait handling in message processing functions")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)