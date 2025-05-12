from typing import Dict, List, Any, Optional, Tuple
from app.core.intent import IntentType, intent_recognizer
from app.core.context import context_manager
from app.integrations.backend_api import backend_client
from app.integrations.llm_service import llm_service

class Orchestrator:
    """Main orchestrator for the AI agent system."""
    
    async def process_message(
        self, 
        message: str, 
        session_id: str = None,
        user_id: str = None,
        user_type: str = None,
    ) -> Dict:
        """
        Process an incoming message from a user.
        
        Args:
            message: The user's message text
            session_id: Optional session ID for existing conversations
            user_id: User ID (required if session_id is not provided)
            user_type: User type ('doctor' or 'patient', required if session_id is not provided)
            
        Returns:
            A response object with the AI's reply and any actions
        """
        # Validate session or create new one
        if not session_id and (not user_id or not user_type):
            raise ValueError("Either session_id or both user_id and user_type must be provided")
        
        if not session_id:
            session_id = context_manager.create_session(user_id, user_type)
        
        session = context_manager.get_session(session_id)
        if not session:
            if not user_id or not user_type:
                raise ValueError("Session not found and user_id/user_type not provided")
            session_id = context_manager.create_session(user_id, user_type)
            session = context_manager.get_session(session_id)
        
        # Get user type from session
        user_type = session.get("user_type")
        user_id = session.get("user_id")
        
        # Add message to history
        context_manager.add_message_to_history(session_id, "user", message)
        
        # Recognize intent
        intent, parameters = await intent_recognizer.recognize_intent(message, user_type)
        
        # Extract patient name from message if needed
        if "patient_id" not in parameters and user_type == "doctor":
            patient_name = self._extract_patient_name(message)
            if patient_name:
                # Try to find the patient by name
                try:
                    patients = await backend_client.find_patient_by_name(patient_name)
                    if patients and len(patients) == 1:
                        parameters["patient_id"] = patients[0].get("id")
                        parameters["patient_name"] = f"{patients[0].get('first_name')} {patients[0].get('last_name')}"
                    elif patients and len(patients) > 1:
                        # Multiple matches, store for context
                        parameters["matched_patients"] = patients
                except Exception as e:
                    print(f"Error finding patient by name: {e}")
        
        # Save intent in session metadata
        context_manager.set_metadata(session_id, "last_intent", intent)
        context_manager.set_metadata(session_id, "intent_parameters", parameters)
        
        # Process based on intent
        response_text, actions = await self._handle_intent(intent, parameters, user_id, user_type, session_id, message)
        
        # Add response to history
        context_manager.add_message_to_history(session_id, "assistant", response_text)
        
        # Prepare response
        response = {
            "text": response_text,
            "session_id": session_id,
            "intent": intent,
            "actions": actions
        }
        
        return response
    
    def _extract_patient_name(self, message: str) -> Optional[str]:
        """Extract a potential patient name from the message."""
        # Simple extraction logic - could be improved with NLP
        message = message.lower()
        
        # Look for phrases that might indicate a patient name
        indicators = [
            "patient information for ",
            "information about ",
            "show me ",
            "tell me about ",
            "what about ",
            "patient ",
            "info for "
        ]
        
        for indicator in indicators:
            if indicator in message:
                pos = message.find(indicator) + len(indicator)
                # Take the next 1-3 words as a potential name
                remaining = message[pos:].strip()
                words = remaining.split()
                if words:
                    if len(words) >= 2:
                        return " ".join(words[:2])  # First and last name
                    else:
                        return words[0]  # Just the first word
        
        return None
    
    async def _handle_intent(
        self, 
        intent: IntentType, 
        parameters: Dict,
        user_id: str,
        user_type: str,
        session_id: str,
        message: str
    ) -> Tuple[str, List[Dict]]:
        """
        Handle a specific intent.
        
        Returns:
            Tuple of (response_text, actions)
        """
        actions = []
        context = {}
        
        # Get conversation history
        history = context_manager.get_history(session_id)
        
        # Handle doctor-specific intents
        if user_type == "doctor":
            if intent == IntentType.DOCTOR_PATIENT_INFO:
                # Get patient info if patient_id is in parameters
                patient_id = parameters.get("patient_id")
                if patient_id:
                    try:
                        patient_data = await backend_client.get_patient(patient_id)
                        context["patient"] = patient_data
                        
                        # Get additional patient information
                        try:
                            allergies = await backend_client.get_patient_allergies(patient_id)
                            context["allergies"] = allergies
                        except Exception as e:
                            print(f"Error getting allergies: {e}")
                        
                        try:
                            medications = await backend_client.get_patient_medications(patient_id)
                            context["medications"] = medications
                        except Exception as e:
                            print(f"Error getting medications: {e}")
                        
                        # Add all patient data to actions for display
                        actions.append({
                            "type": "display_patient_info",
                            "data": {
                                "basic_info": patient_data,
                                "allergies": context.get("allergies", []),
                                "medications": context.get("medications", [])
                            }
                        })
                    except Exception as e:
                        print(f"Error getting patient info: {e}")
                        context["error"] = f"Could not retrieve patient information: {str(e)}"
                elif "matched_patients" in parameters:
                    # Multiple patients matched the name
                    matched_patients = parameters["matched_patients"]
                    context["matched_patients"] = matched_patients
                    actions.append({
                        "type": "display_matched_patients",
                        "data": matched_patients
                    })
            
            elif intent == IntentType.DOCTOR_APPOINTMENT_SCHEDULE:
                try:
                    # Get doctor's schedule
                    schedule = await backend_client.get_doctor_schedule(user_id)
                    context["schedule"] = schedule
                    actions.append({
                        "type": "display_schedule",
                        "data": schedule
                    })
                except Exception as e:
                    print(f"Error getting schedule: {e}")
                    context["error"] = f"Could not retrieve appointment schedule: {str(e)}"
            
            elif intent == IntentType.DOCTOR_MISSED_APPOINTMENTS:
                try:
                    missed = await backend_client.get_missed_appointments(user_id)
                    context["missed_appointments"] = missed
                    actions.append({
                        "type": "display_missed_appointments",
                        "data": missed
                    })
                except Exception as e:
                    print(f"Error getting missed appointments: {e}")
                    context["error"] = f"Could not retrieve missed appointments: {str(e)}"
            
            elif intent == IntentType.DOCTOR_TEST_RESULTS:
                patient_id = parameters.get("patient_id")
                if patient_id:
                    try:
                        test_results = await backend_client.get_patient_test_results(patient_id)
                        
                        # Also get basic patient info for context
                        patient_data = await backend_client.get_patient(patient_id)
                        patient_name = f"{patient_data.get('first_name')} {patient_data.get('last_name')}"
                        
                        context["test_results"] = test_results
                        context["patient_name"] = patient_name
                        actions.append({
                            "type": "display_test_results",
                            "data": {
                                "patient": patient_name,
                                "results": test_results
                            }
                        })
                    except Exception as e:
                        print(f"Error getting test results: {e}")
                        context["error"] = f"Could not retrieve test results: {str(e)}"
        
        # Handle patient-specific intents
        elif user_type == "patient":
            if intent == IntentType.PATIENT_APPOINTMENT_INFO:
                try:
                    # Get patient's appointments
                    appointments = await backend_client.get_appointments({"patient_id": user_id})
                    
                    # Get doctor details for each appointment
                    detailed_appointments = []
                    for appointment in appointments:
                        doctor_id = appointment.get("doctor_id")
                        if doctor_id:
                            try:
                                doctor_name = f"Dr. {doctor.get('first_name')} {doctor.get('last_name')}"
                                doctor_specialty = doctor.get('specialty', '')
                                appointment["doctor_name"] = doctor_name
                                appointment["doctor_specialty"] = doctor_specialty
                            except Exception as e:
                                print(f"Error getting doctor details: {e}")
                                appointment["doctor_name"] = "Unknown"
                        detailed_appointments.append(appointment)
                    
                    context["appointments"] = detailed_appointments
                    actions.append({
                        "type": "display_appointments",
                        "data": detailed_appointments
                    })
                except Exception as e:
                    print(f"Error getting appointments: {e}")
                    context["error"] = f"Could not retrieve appointment information: {str(e)}"
            
            elif intent == IntentType.PATIENT_MEDICATION_INFO:
                try:
                    # Get patient's medications
                    medications = await backend_client.get_patient_medications(user_id)
                    context["medications"] = medications
                    actions.append({
                        "type": "display_medications",
                        "data": medications
                    })
                except Exception as e:
                    print(f"Error getting medication info: {e}")
                    context["error"] = f"Could not retrieve medication information: {str(e)}"
            
            elif intent == IntentType.PATIENT_TEST_RESULTS:
                try:
                    # Get patient's test results
                    test_results = await backend_client.get_patient_test_results(user_id)
                    context["test_results"] = test_results
                    actions.append({
                        "type": "display_test_results",
                        "data": test_results
                    })
                except Exception as e:
                    print(f"Error getting test results: {e}")
                    context["error"] = f"Could not retrieve test results: {str(e)}"
            
            elif intent == IntentType.PATIENT_SCHEDULE_APPOINTMENT:
                try:
                    # Get list of doctors for context
                    doctors = await backend_client.get_doctors()
                    doctor_list = []
                    for doctor in doctors:
                        doctor_list.append({
                            "id": doctor.get("id"),
                            "name": f"Dr. {doctor.get('first_name')} {doctor.get('last_name')}",
                            "specialty": doctor.get("specialty", "General Practice")
                        })
                    
                    context["available_doctors"] = doctor_list
                    actions.append({
                        "type": "initiate_appointment_scheduling",
                        "data": {
                            "message": "Please provide your preferred date, time, and doctor for the appointment.",
                            "available_doctors": doctor_list
                        }
                    })
                except Exception as e:
                    print(f"Error getting doctors for appointment scheduling: {e}")
                    context["error"] = f"Could not retrieve available doctors: {str(e)}"
        
        # Handle general intents
        if intent in [IntentType.GREETING, IntentType.FAREWELL, IntentType.THANKS, IntentType.HELP, IntentType.UNKNOWN]:
            # For general intents, add user type to context
            context["user_type"] = user_type
            
            # For help intent, provide appropriate context
            if intent == IntentType.HELP:
                if user_type == "doctor":
                    context["help_topics"] = [
                        "Viewing patient information",
                        "Checking your appointment schedule",
                        "Viewing missed appointments",
                        "Accessing test results"
                    ]
                elif user_type == "patient":
                    context["help_topics"] = [
                        "Viewing your appointments",
                        "Finding information about your medications",
                        "Accessing your test results",
                        "Scheduling new appointments"
                    ]
        
        # Process the response using the LLM
        system_prompt = None
        if user_type == "doctor":
            system_prompt = """
            You are an AI assistant for a medical clinic system, currently assisting a doctor.
            Your role is to provide information clearly and professionally, focusing on medical accuracy.
            Use medical terminology appropriate for healthcare professionals.
            Be concise but thorough in your responses.
            
            When presenting patient information, organize it clearly with the most important information first.
            When discussing medications or test results, highlight any abnormal values or potential concerns.
            When showing appointments, organize them chronologically and highlight any conflicts or special notes.
            """
        elif user_type == "patient":
            system_prompt = """
            You are an AI assistant for a medical clinic system, currently assisting a patient.
            Your role is to provide clear, easy-to-understand information about healthcare topics.
            Avoid complex medical jargon when possible, and explain medical terms when you use them.
            Be empathetic and supportive in your responses.
            Remember that you are not providing medical advice, only information from the patient's records.
            
            When discussing medications, explain their general purpose in simple terms.
            When discussing test results, focus on whether they are normal or require follow-up.
            When discussing appointments, provide clear details about date, time, location, and doctor.
            """
        
        # Generate response text using the LLM
        response_text = await llm_service.process_chat(
            user_input=message,
            context=context,
            system_prompt=system_prompt,
            history=history
        )
        
        return response_text, actions

# Create a singleton instance
orchestrator = Orchestrator()
#doctor = await backend_client.get_doctor(doctor_id)
                                