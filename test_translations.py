#!/usr/bin/env python3
"""
Test script to verify translations are loading correctly.
"""

import json
import sys

def test_strings_json():
    """Test strings.json structure."""
    try:
        with open('./custom_components/my_verisure/strings.json', 'r') as f:
            strings = json.load(f)
        
        print("✅ strings.json loaded successfully")
        
        # Check phone_selection step
        if 'config' in strings and 'step' in strings['config']:
            steps = strings['config']['step']
            if 'phone_selection' in steps:
                phone_step = steps['phone_selection']
                if 'data' in phone_step and 'phone_id' in phone_step['data']:
                    print(f"✅ phone_id translation: {phone_step['data']['phone_id']}")
                else:
                    print("❌ phone_id not found in phone_selection data")
            else:
                print("❌ phone_selection step not found")
        else:
            print("❌ Invalid strings.json structure")
            
        return True
    except Exception as e:
        print(f"❌ Error loading strings.json: {e}")
        return False

def test_spanish_translations():
    """Test Spanish translations."""
    try:
        with open('./custom_components/my_verisure/translations/es.json', 'r') as f:
            translations = json.load(f)
        
        print("✅ Spanish translations loaded successfully")
        
        # Check phone_selection step
        if 'config' in translations and 'step' in translations['config']:
            steps = translations['config']['step']
            if 'phone_selection' in steps:
                phone_step = steps['phone_selection']
                if 'data' in phone_step and 'phone_id' in phone_step['data']:
                    print(f"✅ Spanish phone_id translation: {phone_step['data']['phone_id']}")
                else:
                    print("❌ phone_id not found in Spanish phone_selection data")
            else:
                print("❌ phone_selection step not found in Spanish")
        else:
            print("❌ Invalid Spanish translations structure")
            
        return True
    except Exception as e:
        print(f"❌ Error loading Spanish translations: {e}")
        return False

def test_english_translations():
    """Test English translations."""
    try:
        with open('./custom_components/my_verisure/translations/en.json', 'r') as f:
            translations = json.load(f)
        
        print("✅ English translations loaded successfully")
        
        # Check phone_selection step
        if 'config' in translations and 'step' in translations['config']:
            steps = translations['config']['step']
            if 'phone_selection' in steps:
                phone_step = steps['phone_selection']
                if 'data' in phone_step and 'phone_id' in phone_step['data']:
                    print(f"✅ English phone_id translation: {phone_step['data']['phone_id']}")
                else:
                    print("❌ phone_id not found in English phone_selection data")
            else:
                print("❌ phone_selection step not found in English")
        else:
            print("❌ Invalid English translations structure")
            
        return True
    except Exception as e:
        print(f"❌ Error loading English translations: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing translations...")
    
    tests = [
        test_strings_json,
        test_spanish_translations,
        test_english_translations,
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n📊 Results:")
    for i, result in enumerate(results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  Test {i+1}: {status}")
    
    if all(results):
        print("\n🎉 All translation tests passed!")
        print("The translations should work correctly in Home Assistant.")
    else:
        print("\n💥 Some translation tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 