#!/usr/bin/env python3
"""
Simple test script to verify all imports work correctly.
"""

import sys

# Add the integration path
sys.path.append('./custom_components/my_verisure')

def test_imports():
    """Test all imports."""
    print("🧪 Testing imports...")
    
    try:
        # Test API imports
        from api.client import MyVerisureClient
        from api.exceptions import MyVerisureError
        print("✅ API imports: OK")
        
        # Test constants
        from const import DOMAIN, CONF_USER, CONF_PASSWORD
        print("✅ Constants imports: OK")
        
        # Test coordinator (will fail due to Home Assistant imports, but that's expected)
        try:
            from coordinator import MyVerisureDataUpdateCoordinator
            print("✅ Coordinator import: OK")
        except ImportError as e:
            if "homeassistant" in str(e):
                print("✅ Coordinator import: Expected failure (Home Assistant not available)")
            else:
                print(f"❌ Coordinator import: Unexpected error - {e}")
        
        # Test config flow (will fail due to Home Assistant imports, but that's expected)
        try:
            from config_flow import MyVerisureConfigFlowHandler
            print("✅ Config flow import: OK")
        except ImportError as e:
            if "homeassistant" in str(e):
                print("✅ Config flow import: Expected failure (Home Assistant not available)")
            else:
                print(f"❌ Config flow import: Unexpected error - {e}")
        
        print("\n🎉 All import tests completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    test_imports() 