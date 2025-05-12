import asyncio
import json
import os
from dotenv import load_dotenv
import httpx
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configuration
API_URL = "http://localhost:8001/api/ai"  # Update with your actual AI agent port
API_KEY = os.getenv("BACKEND_API_KEY", "1")

# Doctor information from seed data
DOCTOR_EMAIL = "doctor@clinic.com"  # Using email for identification
DOCTOR_NAME = "Dr. John Smith"

# Patient information from seed data
PATIENT_EMAIL = "patient@example.com"
PATIENT_NAME = "Jane Doe"

async def test_backend_connectivity():
    """Test direct connectivity to backend API endpoints."""
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    backend_base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
    
    print(f"\n=== Testing Backend Connectivity ===")
    print(f"Backend URL: {backend_base_url}")
    print(f"API Key: {API_KEY}")
    
    async with httpx.AsyncClient() as client:
        # Test authentication
        try:
            print("\nTesting Auth Endpoint...")
            response = await client.get(f"{backend_base_url}/api/auth/check", headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error connecting to backend auth: {e}")
        
        # Test patients endpoint
        try:
            print("\nTesting Patients Endpoint...")
            response = await client.get(f"{backend_base_url}/api/patients", headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                patients = response.json()
                print(f"Found {len(patients)} patients:")
                for i, patient in enumerate(patients):
                    print(f"  Patient {i+1}: {patient.get('first_name')} {patient.get('last_name')} (ID: {patient.get('id')})")
                    print(f"    Email: {patient.get('email')}")
                    
                    # Try to get detailed patient info
                    try:
                        details_response = await client.get(f"{backend_base_url}/api/patients/{patient.get('id')}", headers=headers)
                        if details_response.status_code == 200:
                            details = details_response.json()
                            print(f"    Allergies: {details.get('allergies')}")
                            print(f"    Medications: {details.get('medications')}")
                        else:
                            print(f"    Error getting details: {details_response.status_code}")
                    except Exception as e:
                        print(f"    Error getting details: {e}")
        except Exception as e:
            print(f"Error connecting to backend patients endpoint: {e}")
        
        # Test doctors endpoint
        try:
            print("\nTesting Doctors Endpoint...")
            response = await client.get(f"{backend_base_url}/api/doctors", headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                doctors = response.json()
                print(f"Found {len(doctors)} doctors:")
                for i, doctor in enumerate(doctors):
                    print(f"  Doctor {i+1}: {doctor.get('first_name')} {doctor.get('last_name')} ({doctor.get('specialty')})")
                    print(f"    ID: {doctor.get('id')}")
                    print(f"    Email: {doctor.get('email')}")
        except Exception as e:
            print(f"Error connecting to backend doctors endpoint: {e}")

async def test_patient_name_lookup():
    """Test looking up a patient by name through the AI agent."""
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Create a doctor session
    async with httpx.AsyncClient() as client:
        print("\n=== Testing Patient Name Lookup ===")
        
        # Create a session for doctor
        response = await client.post(
            f"{API_URL}/sessions",
            headers=headers,
            params={"test_user_id": DOCTOR_EMAIL, "test_user_type": "doctor"},
            json={"metadata": {"name": DOCTOR_NAME}}
        )
        
        print(f"Session creation response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return
            
        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"Doctor session created: {session_id}")
        
        # Test patient name lookup
        patient_name = "Jane Doe"  # Using a name instead of ID
        message = f"Show me information about {patient_name}"
        
        print(f"\nDoctor sending: {message}")
        response = await client.post(
            f"{API_URL}/chat",
            headers=headers,
            params={"test_user_id": DOCTOR_EMAIL, "test_user_type": "doctor"},
            json={"message": message, "session_id": session_id}
        )
        
        print(f"Status code: {response.status_code}")
        
        try:
            result = response.json()
            if "error" in result:
                print(f"Error: {result['error']['message']}")
            else:
                print(f"AI response: {result['message']}")
                if result.get("actions"):
                    print(f"Actions: {json.dumps(result['actions'], indent=2)}")
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Raw response: {response.text}")
        
        # Test allergies lookup
        message = f"What allergies does {patient_name} have?"
        
        print(f"\nDoctor sending: {message}")
        response = await client.post(
            f"{API_URL}/chat",
            headers=headers,
            params={"test_user_id": DOCTOR_EMAIL, "test_user_type": "doctor"},
            json={"message": message, "session_id": session_id}
        )
        
        print(f"Status code: {response.status_code}")
        
        try:
            result = response.json()
            if "error" in result:
                print(f"Error: {result['error']['message']}")
            else:
                print(f"AI response: {result['message']}")
                if result.get("actions"):
                    print(f"Actions: {json.dumps(result['actions'], indent=2)}")
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Raw response: {response.text}")

async def main():
    """Run test functions."""
    try:
        await test_backend_connectivity()
        await test_patient_name_lookup()
    except Exception as e:
        print(f"Error in tests: {e}")

if __name__ == "__main__":
    asyncio.run(main())