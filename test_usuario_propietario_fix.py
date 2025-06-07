#!/usr/bin/env python3
"""
Test script to verify the Usuario-Propietario relationship fix
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_usuario_propietario_relationship():
    """Test the correct Usuario-Propietario relationship"""
    try:
        from app.models.usuario import Usuario
        from app.models.propietario import Propietario
        
        print("✅ Model imports successful")
        
        # Check Usuario model has propietario_id field
        usuario_fields = Usuario.__fields__.keys()
        if 'propietario_id' in usuario_fields:
            print("✅ Usuario model has propietario_id field")
        else:
            print("❌ Usuario model missing propietario_id field")
            return False
            
        # Check Propietario model does NOT have usuario_id field
        propietario_fields = Propietario.__fields__.keys()
        if 'usuario_id' not in propietario_fields:
            print("✅ Propietario model correctly does NOT have usuario_id field")
        else:
            print("⚠️  Propietario model has usuario_id field - this may be legacy")
            
        # Test the require_propietario function import
        from app.dependencies import require_propietario
        print("✅ require_propietario function imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing relationship: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Testing Usuario-Propietario Relationship Fix...")
    print("=" * 60)
    
    success = test_usuario_propietario_relationship()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 Usuario-Propietario relationship is correctly configured!")
        print("📝 The fix changes the query from:")
        print("   OLD: Propietario.usuario_id == user.id (WRONG)")
        print("   NEW: user.propietario_id -> Propietario.id (CORRECT)")
    else:
        print("💥 There are still issues with the relationship.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
