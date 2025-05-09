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
                        actions.append({
                            "type": "display_patient_info",
                            "data": patient_data
                        })
                    except Exception as e:
                        print(f"Error getting patient info: {e}")
                        context["error"] = f"Could not retrieve patient information: {str(e)}"
            
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
                        context["test_results"] = test_results
                        actions.append({
                            "type": "display_test_results",
                            "data": test_results
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
                    context["appointments"] = appointments
                    actions.append({
                        "type": "display_appointments",
                        "data": appointments
                    })
                except Exception as e:
                    print(f"Error getting appointments: {e}")
                    context["error"] = f"Could not retrieve appointment information: {str(e)}"
            
            elif intent == IntentType.PATIENT_MEDICATION_INFO:
                try:
                    # Get patient's complete info including medications
                    patient_data = await backend_client.get_patient(user_id)
                    if "medications" in patient_data:
                        context["medications"] = patient_data["medications"]
                        actions.append({
                            "type": "display_medications",
                            "data": patient_data["medications"]
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
                # For this intent, we'll just provide information about how to schedule
                # In a real implementation, we would handle the scheduling flow
                actions.append({
                    "type": "initiate_appointment_scheduling",
                    "data": {
                        "message": "Please provide your preferred date, time, and doctor for the appointment."
                    }
                })
        
        # Handle general intents
        if intent in [IntentType.GREETING, IntentType.FAREWELL, IntentType.THANKS, IntentType.HELP, IntentType.UNKNOWN]:
            # No special context needed for these general intents
            pass
        
        # Process the response using the LLM
        system_prompt = None
        if user_type == "doctor":
            system_prompt = """
            You are an AI assistant for a medical clinic system, currently assisting a doctor.
            Your role is to provide information clearly and professionally, focusing on medical accuracy.
            Use medical terminology appropriate for healthcare professionals.
            Be concise but thorough in your responses.
            """
        elif user_type == "patient":
            system_prompt = """
            You are an AI assistant for a medical clinic system, currently assisting a patient.
            Your role is to provide clear, easy-to-understand information about healthcare topics.
            Avoid complex medical jargon when possible, and explain medical terms when you use them.
            Be empathetic and supportive in your responses.
            Remember that you are not providing medical advice, only information from the patient's records.
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