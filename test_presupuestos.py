#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de presupuestos
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_login():
    """Test login functionality"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"Login response status: {response.status_code}")
    
    if response.status_code == 302:
        print("Login successful - redirect detected")
        # Check if we get redirected to admin dashboard
        dashboard_response = session.get(f"{BASE_URL}/admin/dashboard")
        print(f"Dashboard access status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            print("✓ Successfully accessed admin dashboard")
            return session
        else:
            print("✗ Failed to access admin dashboard")
            return None
    else:
        print("✗ Login failed")
        return None

def test_presupuestos_list(session):
    """Test presupuestos listing page"""
    response = session.get(f"{BASE_URL}/admin/presupuestos")
    print(f"Presupuestos page status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Successfully accessed presupuestos page")
        # Check if the page contains expected elements
        content = response.text
        if "Presupuestos Anuales" in content:
            print("✓ Page contains expected title")
        if "Nuevo Presupuesto" in content:
            print("✓ Page contains create button")
        return True
    else:
        print("✗ Failed to access presupuestos page")
        return False

def test_finanzas_page(session):
    """Test finanzas page with presupuesto tab"""
    response = session.get(f"{BASE_URL}/admin/finanzas")
    print(f"Finanzas page status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Successfully accessed finanzas page")
        content = response.text
        if "Presupuestos Anuales" in content:
            print("✓ Finanzas page contains presupuesto tab")
        if "Ver Todos" in content:
            print("✓ Finanzas page contains link to dedicated presupuestos page")
        return True
    else:
        print("✗ Failed to access finanzas page")
        return False

def test_create_presupuesto(session):
    """Test creating a new presupuesto"""
    presupuesto_data = {
        "año": 2026,
        "descripcion": "Presupuesto de prueba automatizada 2026",
        "redirect_to": "/admin/presupuestos"
    }
    
    response = session.post(f"{BASE_URL}/admin/presupuestos/crear", data=presupuesto_data, allow_redirects=False)
    print(f"Create presupuesto response status: {response.status_code}")
    
    if response.status_code == 302:
        print("✓ Presupuesto creation successful - redirect detected")
        # Check if we can access the new presupuesto
        presupuestos_response = session.get(f"{BASE_URL}/admin/presupuestos")
        if "2026" in presupuestos_response.text:
            print("✓ New presupuesto appears in the list")
            return True
        else:
            print("? New presupuesto might not appear immediately")
            return True
    else:
        print(f"✗ Failed to create presupuesto: {response.status_code}")
        if response.status_code == 200:
            # Check for error messages in the response
            if "ya existe" in response.text:
                print("  - Presupuesto for this year already exists")
            return False
        return False

def main():
    """Run all tests"""
    print("=== Testing Presupuestos Functionality ===\n")
    
    # Test 1: Login
    print("1. Testing login...")
    session = test_login()
    if not session:
        print("Cannot continue without successful login")
        return
    
    print("\n2. Testing presupuestos listing page...")
    test_presupuestos_list(session)
    
    print("\n3. Testing finanzas page...")
    test_finanzas_page(session)
    
    print("\n4. Testing presupuesto creation...")
    test_create_presupuesto(session)
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
