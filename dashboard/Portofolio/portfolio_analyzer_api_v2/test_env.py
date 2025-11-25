#!/usr/bin/env python3
"""Test script to verify .env file is loading correctly"""
import os
from dotenv import load_dotenv

print("=" * 60)
print("TESTING .ENV FILE LOADING")
print("=" * 60)

# Try loading from project root
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"\nLooking for .env at: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    print(f"\nFile size: {os.path.getsize(env_path)} bytes")
    
    # Try loading
    result = load_dotenv(dotenv_path=env_path)
    print(f"load_dotenv() returned: {result}")
    
    # Check what was loaded
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        api_key = api_key.strip().strip('"').strip("'")
        print(f"\n✓ OPENAI_API_KEY found!")
        print(f"  Length: {len(api_key)} characters")
        print(f"  Starts with: {api_key[:10]}...")
        print(f"  Ends with: ...{api_key[-10:]}")
        
        # Test if it's a valid format
        if api_key.startswith('sk-'):
            print("  ✓ Format looks correct (starts with 'sk-')")
        else:
            print("  ⚠️  Format may be incorrect (should start with 'sk-')")
    else:
        print("\n✗ OPENAI_API_KEY not found in environment")
        print("\nPlease verify your .env file contains:")
        print("  OPENAI_API_KEY=sk-your-key-here")
        print("\nOr with quotes:")
        print('  OPENAI_API_KEY="sk-your-key-here"')
else:
    print(f"\n✗ .env file not found at: {env_path}")
    print("  Please create a .env file in the project root with:")
    print("  OPENAI_API_KEY=sk-your-key-here")

print("=" * 60)

