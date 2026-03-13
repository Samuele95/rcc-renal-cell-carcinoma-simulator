#!/usr/bin/env python3
"""Test basic imports without MPI dependencies."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ui_imports():
    """Test UI-related imports that don't require MPI."""
    try:
        print("Testing Streamlit import...")
        import streamlit as st
        print("✅ Streamlit import successful")
        
        print("Testing UI lib imports...")
        from ui.lib.state import load_all_defaults
        from ui.lib.formatting import TREATMENT_LABELS
        from ui.lib.charts import AgentType
        print("✅ UI library imports successful")
        
        print("Testing YAML config loading...")
        defaults = load_all_defaults()
        print(f"✅ Loaded {len(defaults)} default parameters")
        
        print("Testing AgentType enum...")
        print(f"✅ Found {len(list(AgentType))} agent types")
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without running simulation."""
    try:
        print("\nTesting parameter loading...")
        from ui.lib.state import load_all_defaults, load_all_labels
        
        defaults = load_all_defaults()
        labels = load_all_labels()
        
        print(f"✅ Defaults: {len(defaults)} parameters")
        print(f"✅ Labels: {len(labels)} parameter labels")
        
        # Test a few key parameters
        key_params = ["sex", "BMI", "treatment", "max_steps", "volume"]
        for param in key_params:
            if param in defaults:
                print(f"   {param}: {defaults[param]}")
            else:
                print(f"   ⚠️ Missing: {param}")
        
        return True
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing RCC Simulation UI Components")
    print("=" * 50)
    
    success = True
    success &= test_ui_imports()
    success &= test_basic_functionality()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! UI should work correctly.")
        print("\nTo launch the UI, run:")
        print("   python run.py --ui")
        print("   # or")
        print("   streamlit run ui/app.py")
    else:
        print("💥 Some tests failed. Check error messages above.")
        print("\nYou may need to install missing dependencies:")
        print("   pip install -r requirements.txt")
    
    sys.exit(0 if success else 1)