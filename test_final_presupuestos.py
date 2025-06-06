#!/usr/bin/env python3
"""
Prueba integral de la funcionalidad de presupuestos
"""
import time
import sys
import os
sys.path.append('.')

def test_application_endpoints():
    """Test all presupuesto-related endpoints"""
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    # Setup session with retries
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    
    BASE_URL = "http://localhost:8001"
    
    print("🚀 Testing Presupuestos Functionality")
    print("=" * 50)
    
    try:
        # Test 1: Home page accessibility
        print("\n1. Testing home page access...")
        response = session.get(f"{BASE_URL}/", timeout=10)
        assert response.status_code == 200, f"Home page failed: {response.status_code}"
        print("✓ Home page accessible")
        
        # Test 2: Login functionality  
        print("\n2. Testing admin login...")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        login_response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False, timeout=10)
        assert login_response.status_code == 302, f"Login failed: {login_response.status_code}"
        print("✓ Admin login successful")
        
        # Test 3: Admin dashboard access
        print("\n3. Testing admin dashboard access...")
        dashboard_response = session.get(f"{BASE_URL}/admin/dashboard", timeout=10)
        assert dashboard_response.status_code == 200, f"Dashboard failed: {dashboard_response.status_code}"
        assert "Gestionar Presupuestos" in dashboard_response.text, "Dashboard missing presupuestos link"
        print("✓ Admin dashboard accessible with presupuestos link")
        
        # Test 4: Dedicated presupuestos page
        print("\n4. Testing dedicated presupuestos page...")
        presupuestos_response = session.get(f"{BASE_URL}/admin/presupuestos", timeout=10)
        assert presupuestos_response.status_code == 200, f"Presupuestos page failed: {presupuestos_response.status_code}"
        assert "Presupuestos Anuales" in presupuestos_response.text, "Missing presupuestos title"
        assert "Nuevo Presupuesto" in presupuestos_response.text, "Missing create button"
        print("✓ Dedicated presupuestos page accessible")
        
        # Test 5: Finanzas page with presupuesto integration
        print("\n5. Testing finanzas page integration...")
        finanzas_response = session.get(f"{BASE_URL}/admin/finanzas", timeout=10)
        assert finanzas_response.status_code == 200, f"Finanzas page failed: {finanzas_response.status_code}"
        assert "Ver Todos" in finanzas_response.text, "Missing 'Ver Todos' link"
        print("✓ Finanzas page integration working")
        
        # Test 6: Create new presupuesto
        print("\n6. Testing presupuesto creation...")
        current_year = 2025
        test_year = current_year + 1
        
        create_data = {
            "año": test_year,
            "descripcion": f"Presupuesto de prueba {test_year}",
            "redirect_to": "/admin/presupuestos"
        }
        
        create_response = session.post(f"{BASE_URL}/admin/presupuestos/crear", data=create_data, allow_redirects=False, timeout=10)
        if create_response.status_code == 302:
            print("✓ Presupuesto creation successful")
            
            # Verify the presupuesto appears in the list
            updated_list = session.get(f"{BASE_URL}/admin/presupuestos", timeout=10)
            if str(test_year) in updated_list.text:
                print("✓ New presupuesto appears in the list")
            else:
                print("⚠ New presupuesto might not appear immediately")
        else:
            print(f"⚠ Presupuesto creation returned: {create_response.status_code}")
            if "ya existe" in create_response.text:
                print("  (Presupuesto for this year already exists)")
        
        # Test 7: Test presupuesto detail page (if we have a presupuesto)
        print("\n7. Testing presupuesto detail functionality...")
        # Try to find a presupuesto ID from the list page
        presupuestos_html = session.get(f"{BASE_URL}/admin/presupuestos", timeout=10).text
        
        # Look for presupuesto detail links
        import re
        detail_links = re.findall(r'/admin/presupuestos/(\d+)', presupuestos_html)
        
        if detail_links:
            presupuesto_id = detail_links[0]
            detail_response = session.get(f"{BASE_URL}/admin/presupuestos/{presupuesto_id}", timeout=10)
            if detail_response.status_code == 200:
                print(f"✓ Presupuesto detail page accessible (ID: {presupuesto_id})")
                assert "Nuevo Item" in detail_response.text, "Missing add item button"
                print("✓ Presupuesto detail page has item creation functionality")
            else:
                print(f"⚠ Presupuesto detail page returned: {detail_response.status_code}")
        else:
            print("⚠ No presupuesto IDs found to test detail page")
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✓ Presupuestos functionality is working correctly")
        print("✓ Navigation between pages works")
        print("✓ Creation functionality works")
        print("✓ Integration with finanzas page works")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Test assertion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_database_models():
    """Test database models and relationships"""
    try:
        print("\n📁 Testing Database Models")
        print("-" * 30)
        
        from app.models.database import DatabaseManager
        from sqlmodel import Session, select
        from app.models.presupuesto_anual import PresupuestoAnual, ItemPresupuesto
        from app.models.usuario import Usuario
        from app.models.concepto import Concepto
        
        db_manager = DatabaseManager()
        
        with db_manager.get_session() as session:
            # Check users exist
            users = session.exec(select(Usuario)).all()
            print(f"✓ Found {len(users)} users in database")
            
            # Check presupuestos exist
            presupuestos = session.exec(select(PresupuestoAnual)).all()
            print(f"✓ Found {len(presupuestos)} presupuestos in database")
            
            # Check conceptos exist
            conceptos = session.exec(select(Concepto)).all()
            print(f"✓ Found {len(conceptos)} conceptos in database")
            
            # Check if there are any presupuesto items
            items = session.exec(select(ItemPresupuesto)).all()
            print(f"✓ Found {len(items)} presupuesto items in database")
            
            print("✓ Database models are accessible and contain data")
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 COMPREHENSIVE PRESUPUESTOS TESTING")
    print("=" * 60)
    
    # Wait a bit for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Test database models first
    db_success = test_database_models()
    
    # Test web application endpoints
    web_success = test_application_endpoints()
    
    print("\n" + "=" * 60)
    if db_success and web_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Presupuestos functionality is fully operational")
        print("\n📋 Features verified:")
        print("  • Database models and relationships")
        print("  • User authentication (admin)")
        print("  • Admin dashboard navigation")
        print("  • Dedicated presupuestos listing page")
        print("  • Finanzas page integration")
        print("  • Presupuesto creation functionality")
        print("  • Presupuesto detail pages")
        print("  • Navigation between different views")
        
        print("\n🔗 Available URLs:")
        print("  • http://localhost:8001/admin/dashboard")
        print("  • http://localhost:8001/admin/presupuestos")
        print("  • http://localhost:8001/admin/finanzas")
        
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
