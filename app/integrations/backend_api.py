import httpx
import json
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
        # Handle patient lookup more robustly - patient_id could be:
        # 1. A UUID (direct database ID)
        # 2. An email address
        # 3. A name string
        
        # First, try direct lookup if it looks like a UUID
        if len(patient_id) > 30 and "-" in patient_id:  # Simple UUID check
            try:
                return await self._make_request("GET", f"/api/patients/{patient_id}")
            except Exception as e:
                print(f"Direct patient lookup failed: {e}")
        
        # If that fails or it's not a UUID, get all patients and filter
        patients = await self.get_patients()
        
        # Check for email match
        if "@" in patient_id:
            for patient in patients:
                if patient.get("email") == patient_id:
                    try:
                        return await self._make_request("GET", f"/api/patients/{patient.get('id')}")
                    except Exception as e:
                        print(f"Patient lookup by email failed: {e}")
                        return patient  # Return basic info if detailed lookup fails
        
        # Check for name match
        patient_id_lower = patient_id.lower()
        for patient in patients:
            full_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".lower()
            if patient_id_lower in full_name or full_name in patient_id_lower:
                try:
                    return await self._make_request("GET", f"/api/patients/{patient.get('id')}")
                except Exception as e:
                    print(f"Patient lookup by name failed: {e}")
                    return patient  # Return basic info if detailed lookup fails
        
        # If no match found
        raise Exception(f"Patient not found: {patient_id}")
    
    async def create_patient(self, patient_data: Dict) -> Dict:
        """Create a new patient."""
        return await self._make_request("POST", "/api/patients", json_data=patient_data)
    
    async def find_patient_by_name(self, name: str) -> List[Dict]:
        """Find patients by name."""
        patients = await self.get_patients()
        name = name.lower()
        
        matching_patients = []
        for patient in patients:
            first_name = patient.get('first_name', '').lower()
            last_name = patient.get('last_name', '').lower()
            full_name = f"{first_name} {last_name}"
            
            if name in first_name or name in last_name or name in full_name:
                matching_patients.append(patient)
        
        return matching_patients
    
    # Doctor-related methods
    async def get_doctors(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get a list of all doctors."""
        params = {"skip": skip, "limit": limit}
        return await self._make_request("GET", "/api/doctors", params=params)
    
    async def get_doctor(self, doctor_id: str) -> Dict:
        """Get doctor details."""
        # Similar approach as get_patient for robust lookup
        
        # First, try direct lookup if it looks like a UUID
        if len(doctor_id) > 30 and "-" in doctor_id:  # Simple UUID check
            try:
                return await self._make_request("GET", f"/api/doctors/{doctor_id}")
            except Exception as e:
                print(f"Direct doctor lookup failed: {e}")
        
        # If that fails or it's not a UUID, get all doctors and filter
        doctors = await self.get_doctors()
        
        # Check for email match
        if "@" in doctor_id:
            for doctor in doctors:
                if doctor.get("email") == doctor_id:
                    try:
                        return await self._make_request("GET", f"/api/doctors/{doctor.get('id')}")
                    except Exception as e:
                        print(f"Doctor lookup by email failed: {e}")
                        return doctor  # Return basic info if detailed lookup fails
        
        # Check for name match
        doctor_id_lower = doctor_id.lower()
        for doctor in doctors:
            full_name = f"{doctor.get('first_name', '')} {doctor.get('last_name', '')}".lower()
            if doctor_id_lower in full_name or full_name in doctor_id_lower:
                try:
                    return await self._make_request("GET", f"/api/doctors/{doctor.get('id')}")
                except Exception as e:
                    print(f"Doctor lookup by name failed: {e}")
                    return doctor  # Return basic info if detailed lookup fails
        
        # If no match found
        raise Exception(f"Doctor not found: {doctor_id}")
    
    # Appointment-related methods
    async def get_appointments(self, filters: Dict = None) -> List[Dict]:
        """Get a list of appointments with optional filtering."""
        # Handle patient_id if it's not a UUID
        if filters and 'patient_id' in filters and not (len(filters['patient_id']) > 30 and "-" in filters['patient_id']):
            try:
                # Try to get actual patient ID
                if "@" in filters['patient_id'] or " " in filters['patient_id']:
                    patient = await self.get_patient(filters['patient_id'])
                    filters['patient_id'] = patient.get('id')
            except Exception as e:
                print(f"Error converting patient identifier to ID: {e}")
        
        # Handle doctor_id if it's not a UUID
        if filters and 'doctor_id' in filters and not (len(filters['doctor_id']) > 30 and "-" in filters['doctor_id']):
            try:
                # Try to get actual doctor ID
                if "@" in filters['doctor_id'] or " " in filters['doctor_id']:
                    doctor = await self.get_doctor(filters['doctor_id'])
                    filters['doctor_id'] = doctor.get('id')
            except Exception as e:
                print(f"Error converting doctor identifier to ID: {e}")
        
        return await self._make_request("GET", "/api/appointments", params=filters)
    
    async def get_appointment(self, appointment_id: str) -> Dict:
        """Get specific appointment details."""
        return await self._make_request("GET", f"/api/appointments/{appointment_id}")
    
    async def create_appointment(self, appointment_data: Dict) -> Dict:
        """Create a new appointment."""
        # Convert patient/doctor identifiers to IDs if needed
        if 'patient_id' in appointment_data and not (len(appointment_data['patient_id']) > 30 and "-" in appointment_data['patient_id']):
            try:
                patient = await self.get_patient(appointment_data['patient_id'])
                appointment_data['patient_id'] = patient.get('id')
            except Exception as e:
                print(f"Error converting patient identifier to ID: {e}")
        
        if 'doctor_id' in appointment_data and not (len(appointment_data['doctor_id']) > 30 and "-" in appointment_data['doctor_id']):
            try:
                doctor = await self.get_doctor(appointment_data['doctor_id'])
                appointment_data['doctor_id'] = doctor.get('id')
            except Exception as e:
                print(f"Error converting doctor identifier to ID: {e}")
        
        return await self._make_request("POST", "/api/appointments", json_data=appointment_data)
    
    async def get_missed_appointments(self, doctor_id: Optional[str] = None) -> List[Dict]:
        """Get missed appointments, optionally filtered by doctor."""
        filters = {"status": "missed"}
        
        if doctor_id:
            # Convert doctor identifier to ID if needed
            if not (len(doctor_id) > 30 and "-" in doctor_id):
                try:
                    if "@" in doctor_id or " " in doctor_id:
                        doctor = await self.get_doctor(doctor_id)
                        doctor_id = doctor.get('id')
                except Exception as e:
                    print(f"Error converting doctor identifier to ID: {e}")
            
            filters["doctor_id"] = doctor_id
        
        appointments = await self._make_request("GET", "/api/appointments", params=filters)
        
        # Enhance appointments with patient names
        enhanced_appointments = []
        patients_cache = {}  # Cache to avoid repeated lookups
        
        for appointment in appointments:
            enhanced_appointment = appointment.copy()
            
            # Add patient name if not present
            if "patient_name" not in enhanced_appointment and "patient_id" in enhanced_appointment:
                patient_id = enhanced_appointment["patient_id"]
                
                # Use cached patient info if available
                if patient_id in patients_cache:
                    patient = patients_cache[patient_id]
                else:
                    try:
                        patient = await self.get_patient(patient_id)
                        patients_cache[patient_id] = patient
                    except Exception:
                        patient = {"first_name": "Unknown", "last_name": "Patient"}
                
                enhanced_appointment["patient_name"] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}"
            
            enhanced_appointments.append(enhanced_appointment)
        
        return enhanced_appointments
    
    async def get_doctor_schedule(self, doctor_id: str) -> List[Dict]:
        """Get a doctor's schedule."""
        # Convert doctor identifier to ID if needed
        if not (len(doctor_id) > 30 and "-" in doctor_id):
            try:
                if "@" in doctor_id or " " in doctor_id:
                    doctor = await self.get_doctor(doctor_id)
                    doctor_id = doctor.get('id')
            except Exception as e:
                print(f"Error converting doctor identifier to ID: {e}")
        
        appointments = await self._make_request("GET", "/api/appointments", params={"doctor_id": doctor_id})
        
        # Enhance appointments with patient names
        enhanced_appointments = []
        patients_cache = {}  # Cache to avoid repeated lookups
        
        for appointment in appointments:
            enhanced_appointment = appointment.copy()
            
            # Add patient name if not present
            if "patient_name" not in enhanced_appointment and "patient_id" in enhanced_appointment:
                patient_id = enhanced_appointment["patient_id"]
                
                # Use cached patient info if available
                if patient_id in patients_cache:
                    patient = patients_cache[patient_id]
                else:
                    try:
                        patient = await self.get_patient(patient_id)
                        patients_cache[patient_id] = patient
                    except Exception:
                        patient = {"first_name": "Unknown", "last_name": "Patient"}
                
                enhanced_appointment["patient_name"] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}"
            
            enhanced_appointments.append(enhanced_appointment)
        
        return enhanced_appointments
    
    # Medical records methods
    async def get_medical_records(self, patient_id: Optional[str] = None, doctor_id: Optional[str] = None) -> List[Dict]:
        """Get medical records, optionally filtered by patient or doctor."""
        params = {}
        
        # Convert patient_id if needed
        if patient_id:
            if not (len(patient_id) > 30 and "-" in patient_id):
                try:
                    if "@" in patient_id or " " in patient_id:
                        patient = await self.get_patient(patient_id)
                        patient_id = patient.get('id')
                except Exception as e:
                    print(f"Error converting patient identifier to ID: {e}")
            
            params["patient_id"] = patient_id
        
        # Convert doctor_id if needed
        if doctor_id:
            if not (len(doctor_id) > 30 and "-" in doctor_id):
                try:
                    if "@" in doctor_id or " " in doctor_id:
                        doctor = await self.get_doctor(doctor_id)
                        doctor_id = doctor.get('id')
                except Exception as e:
                    print(f"Error converting doctor identifier to ID: {e}")
            
            params["doctor_id"] = doctor_id
        
        return await self._make_request("GET", "/api/medical-records", params=params)
    
    async def create_medical_record(self, record_data: Dict) -> Dict:
        """Create a new medical record."""
        # Convert patient/doctor identifiers to IDs if needed
        if 'patient_id' in record_data and not (len(record_data['patient_id']) > 30 and "-" in record_data['patient_id']):
            try:
                patient = await self.get_patient(record_data['patient_id'])
                record_data['patient_id'] = patient.get('id')
            except Exception as e:
                print(f"Error converting patient identifier to ID: {e}")
        
        if 'doctor_id' in record_data and not (len(record_data['doctor_id']) > 30 and "-" in record_data['doctor_id']):
            try:
                doctor = await self.get_doctor(record_data['doctor_id'])
                record_data['doctor_id'] = doctor.get('id')
            except Exception as e:
                print(f"Error converting doctor identifier to ID: {e}")
        
        return await self._make_request("POST", "/api/medical-records", json_data=record_data)
    
    async def get_patient_test_results(self, patient_id: str) -> List[Dict]:
        """Get patient test results.
        
        Since your backend doesn't have a specific test results endpoint,
        we'll extract test results from medical records.
        """
        # Convert patient identifier to ID if needed
        if not (len(patient_id) > 30 and "-" in patient_id):
            try:
                if "@" in patient_id or " " in patient_id:
                    patient = await self.get_patient(patient_id)
                    patient_id = patient.get('id')
            except Exception as e:
                print(f"Error converting patient identifier to ID: {e}")
                # Continue with original ID, we'll handle possible errors below
        
        try:
            # Get medical records for this patient
            records = await self.get_medical_records(patient_id=patient_id)
            
            # Filter and format records that might contain test results
            test_results = []
            test_keywords = ["test", "lab", "result", "blood", "urine", "scan", "x-ray", "mri", "ct", "ultrasound"]
            
            for record in records:
                # Check if record contains test results
                diagnosis = record.get("diagnosis", "").lower()
                treatment = record.get("treatment", "").lower()
                notes = record.get("notes", "").lower()
                
                is_test_record = any(keyword in diagnosis or keyword in treatment or keyword in notes 
                                   for keyword in test_keywords)
                
                if is_test_record:
                    # Get doctor information
                    doctor_name = "Unknown"
                    try:
                        doctor = await self.get_doctor(record.get("doctor_id"))
                        doctor_name = f"Dr. {doctor.get('first_name')} {doctor.get('last_name')}"
                    except Exception:
                        pass
                    
                    test_results.append({
                        "date": record.get("visit_date"),
                        "doctor": doctor_name,
                        "diagnosis": record.get("diagnosis"),
                        "results": {
                            "treatment": record.get("treatment"),
                            "notes": record.get("notes")
                        }
                    })
            
            return test_results
        except Exception as e:
            print(f"Error retrieving test results: {e}")
            return []
    
    async def get_patient_medical_history(self, patient_id: str) -> List[Dict]:
        """Get patient medical history."""
        # Convert patient identifier to ID if needed
        if not (len(patient_id) > 30 and "-" in patient_id):
            try:
                if "@" in patient_id or " " in patient_id:
                    patient = await self.get_patient(patient_id)
                    patient_id = patient.get('id')
            except Exception as e:
                print(f"Error converting patient identifier to ID: {e}")
        
        try:
            records = await self.get_medical_records(patient_id=patient_id)
            
            # Enhance records with doctor names
            enhanced_records = []
            doctors_cache = {}  # Cache to avoid repeated lookups
            
            for record in records:
                enhanced_record = record.copy()
                
                # Add doctor name if not present
                if "doctor_name" not in enhanced_record and "doctor_id" in enhanced_record:
                    doctor_id = enhanced_record["doctor_id"]
                    
                    # Use cached doctor info if available
                    if doctor_id in doctors_cache:
                        doctor = doctors_cache[doctor_id]
                    else:
                        try:
                            doctor = await self.get_doctor(doctor_id)
                            doctors_cache[doctor_id] = doctor
                        except Exception:
                            doctor = {"first_name": "Unknown", "last_name": "Doctor"}
                    
                    enhanced_record["doctor_name"] = f"Dr. {doctor.get('first_name', '')} {doctor.get('last_name', '')}"
                
                enhanced_records.append(enhanced_record)
            
            # Sort by visit date (newest first)
            enhanced_records.sort(key=lambda x: x.get("visit_date", ""), reverse=True)
            
            return enhanced_records
        except Exception as e:
            print(f"Error retrieving medical history: {e}")
            return []
    
    async def get_patient_medications(self, patient_id: str) -> List[str]:
        """Get a patient's medications."""
        try:
            # First, try to get complete patient info
            patient = await self.get_patient(patient_id)
            
            # Check if medications are stored directly in patient data
            if "medications" in patient:
                # Handle different formats - could be JSON string or already parsed
                medications = patient["medications"]
                if isinstance(medications, str):
                    try:
                        return json.loads(medications)
                    except json.JSONDecodeError:
                        return [medications]  # If not JSON, return as single item list
                elif isinstance(medications, list):
                    return medications
                else:
                    return []
            
            return []
        except Exception as e:
            print(f"Error retrieving medications: {e}")
            return []
    
    async def get_patient_allergies(self, patient_id: str) -> List[str]:
        """Get a patient's allergies."""
        try:
            # First, try to get complete patient info
            patient = await self.get_patient(patient_id)
            
            # Check if allergies are stored directly in patient data
            if "allergies" in patient:
                # Handle different formats - could be JSON string or already parsed
                allergies = patient["allergies"]
                if isinstance(allergies, str):
                    try:
                        return json.loads(allergies)
                    except json.JSONDecodeError:
                        return [allergies]  # If not JSON, return as single item list
                elif isinstance(allergies, list):
                    return allergies
                else:
                    return []
            
            return []
        except Exception as e:
            print(f"Error retrieving allergies: {e}")
            return []
    
    async def get_doctor_patients(self, doctor_id: str) -> List[Dict]:
        """Get a list of a doctor's patients based on appointments."""
        # Convert doctor identifier to ID if needed
        if not (len(doctor_id) > 30 and "-" in doctor_id):
            try:
                if "@" in doctor_id or " " in doctor_id:
                    doctor = await self.get_doctor(doctor_id)
                    doctor_id = doctor.get('id')
            except Exception as e:
                print(f"Error converting doctor identifier to ID: {e}")
        
        try:
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
        except Exception as e:
            print(f"Error retrieving doctor's patients: {e}")
            return []

# Create a singleton instance
backend_client = BackendAPIClient()