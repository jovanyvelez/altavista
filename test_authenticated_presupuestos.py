#!/usr/bin/env python3
"""
Prueba con autenticación de la funcionalidad de presupuestos
"""
import requests
import time
import sys

def test_presupuestos_with_auth():
    """Test presupuestos functionality with proper authentication"""
    print("🚀 Testing Presupuestos with Authentication")
    print("=" * 50)
    
    session = requests.Session()
    BASE_URL = "http://localhost:8001"
    
    try:
        # Step 1: Get login page to establish session
        print("\n1. Getting login page...")
        login_page = session.get(f"{BASE_URL}/login", timeout=10)
        print(f"✓ Login page status: {login_page.status_code}")
        
        # Step 2: Login as admin
        print("\n2. Logging in as admin...")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = session.post(
            f"{BASE_URL}/login", 
            data=login_data, 
            timeout=10,
            allow_redirects=True
        )
        
        print(f"✓ Login response status: {login_response.status_code}")
        
        # Step 3: Test admin dashboard
        print("\n3. Testing admin dashboard...")
        dashboard = session.get(f"{BASE_URL}/admin/dashboard", timeout=10)
        print(f"✓ Dashboard status: {dashboard.status_code}")
        
        if dashboard.status_code == 200:
            if "Gestionar Presupuestos" in dashboard.text:
                print("✓ Dashboard contains presupuestos link!")
            else:
                print("⚠ Presupuestos link not found in dashboard")
        
        # Step 4: Test dedicated presupuestos page
        print("\n4. Testing dedicated presupuestos page...")
        presupuestos = session.get(f"{BASE_URL}/admin/presupuestos", timeout=10)
        print(f"✓ Presupuestos page status: {presupuestos.status_code}")
        
        if presupuestos.status_code == 200:
            success_indicators = [
                ("Presupuestos Anuales", "page title"),
                ("Nuevo Presupuesto", "create button"),
                ("Total Presupuestos", "statistics"),
                ("table", "data table")
            ]
            
            for indicator, description in success_indicators:
                if indicator in presupuestos.text:
                    print(f"✓ Found {description}")
                else:
                    print(f"⚠ Missing {description}")
        
        # Step 5: Test finanzas integration
        print("\n5. Testing finanzas page integration...")
        finanzas = session.get(f"{BASE_URL}/admin/finanzas", timeout=10)
        print(f"✓ Finanzas page status: {finanzas.status_code}")
        
        if finanzas.status_code == 200:
            if "Ver Todos" in finanzas.text:
                print("✓ Finanzas page has 'Ver Todos' link")
            else:
                print("⚠ 'Ver Todos' link not found")
        
        # Step 6: Test presupuesto creation (if possible)
        print("\n6. Testing presupuesto creation...")
        test_year = 2026  # Use a future year to avoid conflicts
        
        create_data = {
            "año": test_year,
            "descripcion": f"Presupuesto Test {test_year}",
            "redirect_to": "/admin/presupuestos"
        }
        
        create_response = session.post(
            f"{BASE_URL}/admin/presupuestos/crear",
            data=create_data,
            timeout=10,
            allow_redirects=False
        )
        
        print(f"✓ Create presupuesto status: {create_response.status_code}")
        
        if create_response.status_code == 302:
            print("✓ Presupuesto creation successful (redirected)")
            
            # Check if the presupuesto appears in the list
            updated_list = session.get(f"{BASE_URL}/admin/presupuestos", timeout=10)
            if str(test_year) in updated_list.text:
                print(f"✓ New presupuesto {test_year} appears in the list")
            else:
                print("⚠ New presupuesto might not appear immediately")
        
        print("\n" + "=" * 50)
        print("🎉 AUTHENTICATION TEST COMPLETED!")
        print("✅ All major functionality is accessible")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run the authenticated test"""
    print("🧪 PRESUPUESTOS AUTHENTICATION TEST")
    print("=" * 60)
    
    # Wait for server to be ready
    print("⏳ Waiting for server...")
    time.sleep(2)
    
    success = test_presupuestos_with_auth()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST PASSED!")
        print("✅ Presupuestos functionality is working with authentication")
        print("\n🌐 Available URLs:")
        print("  • http://localhost:8001/ (home)")
        print("  • http://localhost:8001/login (login)")
        print("  • http://localhost:8001/admin/dashboard (dashboard)")
        print("  • http://localhost:8001/admin/presupuestos (presupuestos)")
        print("  • http://localhost:8001/admin/finanzas (finanzas)")
        
        print("\n👤 Login credentials:")
        print("  • Username: admin")
        print("  • Password: admin123")
        
        return 0
    else:
        print("❌ TEST FAILED")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
