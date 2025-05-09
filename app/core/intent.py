from typing import Dict, List, Tuple
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from config import config

class IntentType(str, Enum):
    # Doctor intents
    DOCTOR_PATIENT_INFO = "doctor_patient_info"
    DOCTOR_APPOINTMENT_SCHEDULE = "doctor_appointment_schedule"
    DOCTOR_MISSED_APPOINTMENTS = "doctor_missed_appointments"
    DOCTOR_TEST_RESULTS = "doctor_test_results"
    
    # Patient intents
    PATIENT_APPOINTMENT_INFO = "patient_appointment_info"
    PATIENT_MEDICATION_INFO = "patient_medication_info"
    PATIENT_TEST_RESULTS = "patient_test_results"
    PATIENT_SCHEDULE_APPOINTMENT = "patient_schedule_appointment"
    
    # General intents
    GREETING = "greeting"
    FAREWELL = "farewell"
    THANKS = "thanks"
    HELP = "help"
    UNKNOWN = "unknown"

class IntentRecognizer:
    """Recognizes user intents from text input."""
    
    def __init__(self):
        self.api_key = config.llm.api_key
        self.model = config.llm.model
        self.base_url =config.llm.base_url
        self.llm = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.0,  # Zero temperature for deterministic output
        )
    
    async def recognize_intent(
        self, text: str, user_type: str
    ) -> Tuple[IntentType, Dict]:
        """
        Recognize the intent from user text.
        
        Args:
            text: The user's input text
            user_type: Either 'doctor' or 'patient'
            
        Returns:
            A tuple of (intent_type, parameters)
        """
        system_prompt = f"""
        You are an intent recognition system for a medical clinic AI assistant.
        The user is a {user_type} interacting with the system.
        
        Analyze the user's input and determine their intent based on the following options:
        
        Doctor intents:
        - doctor_patient_info: Doctor wants information about a patient
        - doctor_appointment_schedule: Doctor wants to view their appointment schedule
        - doctor_missed_appointments: Doctor wants to see missed appointments
        - doctor_test_results: Doctor wants to see patient test results
        
        Patient intents:
        - patient_appointment_info: Patient wants information about their appointments
        - patient_medication_info: Patient wants information about their medications
        - patient_test_results: Patient wants to see their test results
        - patient_schedule_appointment: Patient wants to schedule an appointment
        
        General intents:
        - greeting: User is greeting the system
        - farewell: User is saying goodbye
        - thanks: User is expressing gratitude
        - help: User needs help with using the system
        - unknown: Intent cannot be determined
        
        Also extract any parameters from the input, such as:
        - patient_id: If a specific patient is mentioned
        - appointment_id: If a specific appointment is mentioned
        - date: If a specific date is mentioned
        - test_type: If a specific type of test is mentioned
        
        Respond with a JSON object containing:
        1. "intent": One of the intent options listed above
        2. "parameters": An object containing extracted parameters
        3. "confidence": A value from 0.0 to 1.0 indicating confidence level
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=text)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse the response as JSON
        try:
            import json
            result = json.loads(response.content)
            
            # Validate the result
            intent = result.get("intent", "unknown")
            parameters = result.get("parameters", {})
            
            # Convert to IntentType enum
            try:
                intent_type = IntentType(intent)
            except ValueError:
                intent_type = IntentType.UNKNOWN
                
            return intent_type, parameters
            
        except Exception as e:
            print(f"Error parsing intent: {e}")
            return IntentType.UNKNOWN, {}
    
    def get_follow_up_questions(self, intent: IntentType) -> List[str]:
        """Get follow-up questions based on the recognized intent."""
        follow_ups = {
            IntentType.DOCTOR_PATIENT_INFO: [
                "Which patient would you like information about?",
                "What specific information do you need about this patient?"
            ],
            IntentType.DOCTOR_APPOINTMENT_SCHEDULE: [
                "Which date would you like to check?",
                "Would you like to see all appointments or just specific types?"
            ],
            IntentType.PATIENT_APPOINTMENT_INFO: [
                "Would you like to see your upcoming appointments?",
                "Are you looking for a specific appointment?"
            ],
            IntentType.PATIENT_SCHEDULE_APPOINTMENT: [
                "What type of appointment would you like to schedule?",
                "Do you have a preferred date and time?"
            ],
        }
        
        return follow_ups.get(intent, ["How can I assist you further?"])

# Create a singleton instance
intent_recognizer = IntentRecognizer()