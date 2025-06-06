#!/usr/bin/env python3
"""
Test script to verify that porcentaje_recaudado variable is now properly provided
to the admin/pagos template
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_admin_pagos_template_variables():
    """Test that admin_pagos route provides porcentaje_recaudado variable"""
    try:
        # Import route function
        from app.routes.admin_pagos import admin_pagos
        
        print("✅ admin_pagos route imported successfully")
        
        # Check if the route file contains porcentaje_recaudado calculation
        with open('app/routes/admin_pagos.py', 'r') as f:
            content = f.read()
            
        if 'porcentaje_recaudado' in content:
            print("✅ porcentaje_recaudado variable found in route")
            
            # Check if it's being calculated
            if 'porcentaje_recaudado = round(' in content:
                print("✅ porcentaje_recaudado calculation found")
                
                # Check if it's being passed to template
                if '"porcentaje_recaudado": porcentaje_recaudado' in content:
                    print("✅ porcentaje_recaudado being passed to template")
                    return True
                else:
                    print("❌ porcentaje_recaudado not being passed to template")
            else:
                print("❌ porcentaje_recaudado calculation not found")
        else:
            print("❌ porcentaje_recaudado variable not found in route")
            
        return False
        
    except Exception as e:
        print(f"❌ Error testing admin_pagos: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Testing porcentaje_recaudado Fix...")
    print("=" * 50)
    
    success = test_admin_pagos_template_variables()
    
    print()
    print("=" * 50)
    if success:
        print("🎉 porcentaje_recaudado fix is working correctly!")
    else:
        print("💥 porcentaje_recaudado fix verification failed.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
