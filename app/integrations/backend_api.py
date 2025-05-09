import httpx
from typing import Dict, List, Any, Optional
from config import config

class BackendAPIClient:
    """Client for interacting with the medical system backend API."""
    
    def __init__(self):
        self.base_url = config.backend.base_url
        self.api_key = config.backend.api_key
        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
    
    async def _make_request(
        self, method: str, endpoint: str, 
        params: Dict = None, json_data: Dict = None
    ) -> Any:
        """Make an HTTP request to the backend API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=self.headers,
                timeout=30.0,
            )
            
            try:
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Log error and handle appropriately
                print(f"HTTP error: {e}")
                # Try to parse error response
                try:
                    error_data = response.json().get("error", {})
                    error_message = error_data.get("message", str(e))
                    print(f"Error details: {error_message}")
                except Exception:
                    error_message = str(e)
                
                raise Exception(f"Backend API error: {error_message}")
    
    async def check_connection(self) -> bool:
        """Check if the connection to the backend API is working."""
        try:
            result = await self._make_request("GET", "/api/auth/check")
            return result.get("status") == "authenticated"
        except Exception as e:
            print(f"Connection check failed: {e}")
            return False
    
    # Patient-related methods
    async def get_patients(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get a list of all patients."""
        params = {"skip": skip, "limit": limit}
        return await self._make_request("GET", "/api/patients", params=params)
    
    async def get_patient(self, patient_id: str) -> Dict:
        """Get complete patient information."""
        return await self._make_request("GET", f"/api/patients/{patient_id}")
    
    async def create_patient(self, patient_data: Dict) -> Dict:
        """Create a new patient."""
        return await self._make_request("POST", "/api/patients", json_data=patient_data)
    
    async def find_patient_by_name(self, name: str) -> List[Dict]:
        """Find patients by name."""
        patients = await self.get_patients()
        name = name.lower()
        
        matching_patients = []
        for patient in patients:
            if (name in patient.get("first_name", "").lower() or 
                name in patient.get("last_name", "").lower()):
                matching_patients.append(patient)
        
        return matching_patients
    
    # Doctor-related methods
    async def get_doctors(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get a list of all doctors."""
        params = {"skip": skip, "limit": limit}
        return await self._make_request("GET", "/api/doctors", params=params)
    
    async def get_doctor(self, doctor_id: str) -> Dict:
        """Get doctor details."""
        return await self._make_request("GET", f"/api/doctors/{doctor_id}")
    
    # Appointment-related methods
    async def get_appointments(self, filters: Dict = None) -> List[Dict]:
        """Get a list of appointments with optional filtering."""
        return await self._make_request("GET", "/api/appointments", params=filters)
    
    async def get_appointment(self, appointment_id: str) -> Dict:
        """Get specific appointment details."""
        return await self._make_request("GET", f"/api/appointments/{appointment_id}")
    
    async def create_appointment(self, appointment_data: Dict) -> Dict:
        """Create a new appointment."""
        return await self._make_request("POST", "/api/appointments", json_data=appointment_data)
    
    async def get_missed_appointments(self, doctor_id: Optional[str] = None) -> List[Dict]:
        """Get missed appointments, optionally filtered by doctor."""
        params = {
            "status": "missed",
            "doctor_id": doctor_id
        }
        return await self._make_request("GET", "/api/appointments", params=params)
    
    async def get_doctor_schedule(self, doctor_id: str) -> List[Dict]:
        """Get a doctor's schedule."""
        return await self._make_request("GET", "/api/appointments", params={"doctor_id": doctor_id})
    
    # Medical records methods
    async def get_medical_records(self, patient_id: Optional[str] = None, doctor_id: Optional[str] = None) -> List[Dict]:
        """Get medical records, optionally filtered by patient or doctor."""
        params = {}
        if patient_id:
            params["patient_id"] = patient_id
        if doctor_id:
            params["doctor_id"] = doctor_id
            
        return await self._make_request("GET", "/api/medical-records", params=params)
    
    async def create_medical_record(self, record_data: Dict) -> Dict:
        """Create a new medical record."""
        return await self._make_request("POST", "/api/medical-records", json_data=record_data)
    
    async def get_patient_test_results(self, patient_id: str) -> List[Dict]:
        """Get patient test results. 
        Note: This assumes test results are part of medical records or implements the endpoint if available."""
        # In a real implementation, this would need to be adjusted based on how the 
        # backend actually stores and returns test results
        records = await self.get_medical_records(patient_id=patient_id)
        
        # Filter records to extract test results
        # This is an example assuming test results are embedded in medical records
        test_results = []
        for record in records:
            if "test_results" in record:
                test_results.append({
                    "date": record.get("visit_date"),
                    "doctor": record.get("doctor_id"),
                    "results": record.get("test_results")
                })
                
        return test_results
    
    async def get_patient_medical_history(self, patient_id: str) -> List[Dict]:
        """Get patient medical history."""
        records = await self.get_medical_records(patient_id=patient_id)
        
        # Sort by visit date (newest first)
        records.sort(key=lambda x: x.get("visit_date", ""), reverse=True)
        
        return records
    
    async def get_doctor_patients(self, doctor_id: str) -> List[Dict]:
        """Get a list of a doctor's patients based on appointments."""
        # First, get all appointments for this doctor
        appointments = await self.get_appointments({"doctor_id": doctor_id})
        
        # Extract unique patient IDs
        patient_ids = set([apt.get("patient_id") for apt in appointments if "patient_id" in apt])
        
        # Get patient details for each patient
        patients = []
        for patient_id in patient_ids:
            try:
                patient = await self.get_patient(patient_id)
                patients.append(patient)
            except Exception as e:
                print(f"Error getting patient {patient_id}: {e}")
                
        return patients

# Create a singleton instance
backend_client = BackendAPIClient()