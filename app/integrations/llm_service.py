from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from config import config

class LLMService:
    """Service for interacting with LLM models."""
    
    def __init__(self):
        self.api_key = config.llm.api_key
        self.model = config.llm.model
        self.base_url = config.llm.base_url
        self.llm = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.2,  # Lower temperature for more deterministic outputs
        )
    
    async def process_chat(
        self, 
        user_input: str, 
        context: Optional[Dict] = None, 
        system_prompt: str = None,
        history: List[Dict] = None
    ) -> str:
        """Process a chat message with the LLM."""
        # Default system prompt for medical context
        if system_prompt is None:
            system_prompt = """
            You are an AI assistant for a medical clinic system. Your role is to assist:
            1. Doctors by providing patient information, appointment summaries, and clinical insights
            2. Patients by answering questions about their healthcare, appointments, and medications
            
            Always be professional, accurate, and compassionate in your responses.
            Never provide medical advice beyond what's in the patient records.
            Maintain patient confidentiality and privacy at all times.
            """
        
        # Build the messages list
        messages = [SystemMessage(content=system_prompt)]
        
        # Add chat history if provided
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Add context if provided
        if context:
            context_str = "Context information:\n"
            for key, value in context.items():
                if isinstance(value, (list, dict)):
                    import json
                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_str = str(value)
                context_str += f"{key}: {value_str}\n"
            messages.append(SystemMessage(content=context_str))
        
        # Add the current user input
        messages.append(HumanMessage(content=user_input))
        
        # Get the response from the LLM
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def analyze_medical_data(
        self, 
        patient_data: Dict,
        query: str
    ) -> str:
        """Analyze patient medical data with a specific query."""
        system_prompt = """
        You are a medical data analysis assistant. Your task is to analyze the provided 
        patient data and respond to the specific query. Base your analysis only on the 
        provided data and avoid making assumptions. If you cannot answer based on the 
        provided data, clearly state this.
        
        Remember that your analysis may be used by healthcare professionals, so be precise,
        factual, and avoid speculative conclusions.
        """
        
        # Format patient data for the prompt
        patient_data_formatted = "\n".join([
            f"{key}: {value}" for key, value in patient_data.items()
        ])
        
        user_message = f"""
        Patient Data:
        {patient_data_formatted}
        
        Query: {query}
        
        Please analyze the above patient data in response to the query.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def summarize_medical_record(self, record: Dict) -> str:
        """Generate a concise summary of a medical record."""
        system_prompt = """
        You are a medical summarization assistant. Create a clear, concise summary of the 
        provided medical record. Focus on key diagnoses, treatments, medications, and 
        important clinical findings. Use professional medical terminology but ensure the 
        summary is accessible to healthcare professionals of different specialties.
        """
        
        # Format the record for the prompt
        record_formatted = "\n".join([
            f"{key}: {value}" for key, value in record.items()
        ])
        
        user_message = f"""
        Medical Record:
        {record_formatted}
        
        Please provide a concise summary of this medical record.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content

# Create a singleton instance
llm_service = LLMService()