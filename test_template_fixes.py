#!/usr/bin/env python3
"""
Test script to verify template-route consistency fixes
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all route modules can be imported without errors"""
    try:
        from app.routes import admin, admin_pagos, propietario, auth
        print("✅ All route modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_template_variables():
    """Test that critical template variables are defined in functions"""
    
    # Check admin_pagos_configuracion has 'meses'
    try:
        from app.routes.admin_pagos import admin_pagos_configuracion
        import inspect
        source = inspect.getsource(admin_pagos_configuracion)
        if '"meses"' in source and '"Enero"' in source:
            print("✅ admin_pagos_configuracion includes 'meses' variable")
        else:
            print("❌ admin_pagos_configuracion missing 'meses' variable")
            return False
    except Exception as e:
        print(f"❌ Error checking admin_pagos_configuracion: {e}")
        return False
    
    # Check admin_pagos_generar_cargos has 'conceptos_cuota'
    try:
        from app.routes.admin_pagos import admin_pagos_generar_cargos
        source = inspect.getsource(admin_pagos_generar_cargos)
        if '"conceptos_cuota"' in source:
            print("✅ admin_pagos_generar_cargos includes 'conceptos_cuota' variable")
        else:
            print("❌ admin_pagos_generar_cargos missing 'conceptos_cuota' variable")
            return False
    except Exception as e:
        print(f"❌ Error checking admin_pagos_generar_cargos: {e}")
        return False
        
    # Check admin_pagos_procesar has 'apartamentos_con_saldo'
    try:
        from app.routes.admin_pagos import admin_pagos_procesar
        source = inspect.getsource(admin_pagos_procesar)
        if '"apartamentos_con_saldo"' in source:
            print("✅ admin_pagos_procesar includes 'apartamentos_con_saldo' variable")
        else:
            print("❌ admin_pagos_procesar missing 'apartamentos_con_saldo' variable")
            return False
    except Exception as e:
        print(f"❌ Error checking admin_pagos_procesar: {e}")
        return False
    
    # Check propietario_mis_pagos has required variables
    try:
        from app.routes.propietario import propietario_mis_pagos
        source = inspect.getsource(propietario_mis_pagos)
        required_vars = ['"saldo_total"', '"total_cargos"', '"total_abonos"', '"estados_pago"']
        missing_vars = []
        for var in required_vars:
            if var not in source:
                missing_vars.append(var)
        
        if not missing_vars:
            print("✅ propietario_mis_pagos includes all required variables")
        else:
            print(f"❌ propietario_mis_pagos missing variables: {missing_vars}")
            return False
    except Exception as e:
        print(f"❌ Error checking propietario_mis_pagos: {e}")
        return False
    
    # Check property naming consistency in admin routes
    try:
        from app.routes.admin import crear_propietario, editar_propietario
        
        crear_source = inspect.getsource(crear_propietario)
        editar_source = inspect.getsource(editar_propietario)
        
        if 'nombre_completo: str = Form' in crear_source:
            print("✅ crear_propietario uses 'nombre_completo' parameter")
        else:
            print("❌ crear_propietario should use 'nombre_completo' parameter")
            return False
            
        if 'nombre_completo: str = Form' in editar_source:
            print("✅ editar_propietario uses 'nombre_completo' parameter")
        else:
            print("❌ editar_propietario should use 'nombre_completo' parameter")
            return False
            
    except Exception as e:
        print(f"❌ Error checking property naming: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 Running Template-Route Consistency Tests...")
    print("=" * 50)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    print()
    
    # Test template variables
    if not test_template_variables():
        all_passed = False
    
    print()
    print("=" * 50)
    if all_passed:
        print("🎉 All tests passed! Template-route consistency fixes are working.")
    else:
        print("💥 Some tests failed. Please review the issues above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
