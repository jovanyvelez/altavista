#!/usr/bin/env python3
"""
Direct test of the admin_pagos route to verify CuotaConfiguracion fix
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_cuota_configuracion_model():
    """Test the CuotaConfiguracion model directly"""
    try:
        from app.models.cuota_configuracion import CuotaConfiguracion
        from decimal import Decimal
        
        # Test creating an instance with the correct attribute name
        config = CuotaConfiguracion(
            apartamento_id=1,
            año=2025,
            mes=6,
            monto_cuota_ordinaria_mensual=Decimal('150000.00')
        )
        
        # Test accessing the attribute
        monto = config.monto_cuota_ordinaria_mensual
        print(f"✅ CuotaConfiguracion model works correctly")
        print(f"✅ Attribute monto_cuota_ordinaria_mensual: {monto}")
        return True
        
    except Exception as e:
        print(f"❌ Error with CuotaConfiguracion model: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_admin_pagos_import():
    """Test importing the admin_pagos route"""
    try:
        from app.routes.admin_pagos import admin_pagos
        print("✅ admin_pagos route imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing admin_pagos: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Testing CuotaConfiguracion Attribute Fix...")
    print("=" * 50)
    
    success = True
    
    # Test model
    if not test_cuota_configuracion_model():
        success = False
    
    print()
    
    # Test route import
    if not test_admin_pagos_import():
        success = False
    
    print()
    print("=" * 50)
    if success:
        print("🎉 All tests passed! CuotaConfiguracion attribute fix is working.")
    else:
        print("💥 Some tests failed. Review the issues above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
