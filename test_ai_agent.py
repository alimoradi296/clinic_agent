import asyncio
import json
import os
from dotenv import load_dotenv
import httpx
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configuration
API_URL = "http://localhost:8001/api/ai"  # Update with your actual port
API_KEY = os.getenv("BACKEND_API_KEY", "1")  # Default API key from documentation

# Doctor information from seed data
DOCTOR_ID = "doctor@clinic.com"  # Using email as ID for simplicity
DOCTOR_NAME = "Dr. John Smith"
DOCTOR_SPECIALTY = "Cardiology"

# Patient information from seed data
PATIENT_ID = "patient@example.com"  # Using email as ID for simplicity
PATIENT_NAME = "Jane Doe"
PATIENT_DOB = "1985-05-15"
PATIENT_ALLERGIES = ["Penicillin", "Peanuts"]
PATIENT_MEDICATIONS = ["Lisinopril 10mg", "Vitamin D"]

async def test_doctor_chat():
    """Test the AI agent as a doctor."""
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Create a session
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/sessions",
            headers=headers,
            params={"test_user_id": DOCTOR_ID, "test_user_type": "doctor"},
            json={"metadata": {"name": DOCTOR_NAME, "specialty": DOCTOR_SPECIALTY}}
        )
        
        print(f"Session creation response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return
            
        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"Doctor session created: {session_id}")
        
        # Test some doctor interactions with real patient data
        messages = [
            f"Show me {PATIENT_NAME}'s information",
            f"What allergies does {PATIENT_NAME} have?",
            f"List the medications that {PATIENT_NAME} is currently taking",
            "Show me my schedule for today",
            "What appointments do I have this week?",
            "Show me any missed appointments"
        ]
        
        for message in messages:
            print(f"\nDoctor sending: {message}")
            response = await client.post(
                f"{API_URL}/chat",
                headers=headers,
                params={"test_user_id": DOCTOR_ID, "test_user_type": "doctor"},
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

async def test_patient_chat():
    """Test the AI agent as a patient."""
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Create a session
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/sessions",
            headers=headers,
            params={"test_user_id": PATIENT_ID, "test_user_type": "patient"},
            json={"metadata": {"name": PATIENT_NAME, "dob": PATIENT_DOB}}
        )
        
        print(f"Session creation response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return
            
        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"Patient session created: {session_id}")
        
        # Test some patient interactions with real data
        messages = [
            "What medications am I currently taking?",
            "What allergies do I have in my record?",
            "When is my next appointment?",
            "Can I schedule an appointment with Dr. Sarah Johnson?",
            "Show me my medical history",
            "What were the results of my last blood test?"
        ]
        
        for message in messages:
            print(f"\nPatient sending: {message}")
            response = await client.post(
                f"{API_URL}/chat",
                headers=headers,
                params={"test_user_id": PATIENT_ID, "test_user_type": "patient"},
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

async def test_backend_connectivity():
    """Test direct connectivity to backend API endpoints."""
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    backend_base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
    
    async with httpx.AsyncClient() as client:
        # Test authentication
        try:
            response = await client.get(f"{backend_base_url}/api/auth/check", headers=headers)
            print(f"\nBackend auth check: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error connecting to backend auth: {e}")
        
        # Test patients endpoint
        try:
            response = await client.get(f"{backend_base_url}/api/patients", headers=headers)
            print(f"\nBackend patients endpoint: {response.status_code}")
            if response.status_code == 200:
                patients = response.json()
                print(f"Found {len(patients)} patients")
                for i, patient in enumerate(patients):
                    print(f"Patient {i+1}: {patient.get('first_name')} {patient.get('last_name')}")
        except Exception as e:
            print(f"Error connecting to backend patients endpoint: {e}")
        
        # Test doctors endpoint
        try:
            response = await client.get(f"{backend_base_url}/api/doctors", headers=headers)
            print(f"\nBackend doctors endpoint: {response.status_code}")
            if response.status_code == 200:
                doctors = response.json()
                print(f"Found {len(doctors)} doctors")
                for i, doctor in enumerate(doctors):
                    print(f"Doctor {i+1}: {doctor.get('first_name')} {doctor.get('last_name')} ({doctor.get('specialty')})")
        except Exception as e:
            print(f"Error connecting to backend doctors endpoint: {e}")

async def main():
    """Run test functions."""
    print("=== Testing Backend Connectivity ===")
    await test_backend_connectivity()
    
    print("\n=== Testing Doctor Interactions ===")
    await test_doctor_chat()
    
    print("\n=== Testing Patient Interactions ===")
    await test_patient_chat()

if __name__ == "__main__":
    asyncio.run(main())