"""Chat client abstraction for different AI providers."""

import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()


class ChatMessage:
    """Standard chat message format."""
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class ChatClient(ABC):
    """Abstract base class for chat clients."""
    
    @abstractmethod
    def chat(self, messages: List[ChatMessage], **kwargs) -> str:
        """Send messages and get response."""
        pass


class AzureChatClient(ChatClient):
    """Azure AI Inference chat client."""
    
    def __init__(self, model: str = "mistral-small"):
        from azure.ai.inference import ChatCompletionsClient
        from azure.core.credentials import AzureKeyCredential
        
        self.model = model
        self.client = ChatCompletionsClient(
            endpoint=os.getenv("AZURE_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AZURE_API_KEY")),
            api_version=os.getenv("AZURE_API_VERSION", "2024-05-01-preview")
        )
    
    def chat(self, messages: List[ChatMessage], **kwargs) -> str:
        """Send messages to Azure AI and return response."""
        message_dicts = [msg.to_dict() for msg in messages]
        
        response = self.client.complete(
            messages=message_dicts,
            model=self.model,
            **kwargs
        )
        
        return response.choices[0].message.content


class OpenAIChatClient(ChatClient):
    """OpenAI chat client."""
    
    def __init__(self, model: str = "gpt-4"):
        import openai
        self.model = model
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def chat(self, messages: List[ChatMessage], **kwargs) -> str:
        """Send messages to OpenAI and return response."""
        message_dicts = [msg.to_dict() for msg in messages]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=message_dicts,
            **kwargs
        )
        
        return response.choices[0].message.content


def get_chat_client(provider: str = "azure", model: Optional[str] = None) -> ChatClient:
    """Factory function to get chat client."""
    if model is None:
        model = os.getenv("DEFAULT_MODEL", "mistral-small")
    
    if provider == "azure":
        return AzureChatClient(model=model)
    elif provider == "openai":
        return OpenAIChatClient(model=model)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def create_message(role: str, content: str) -> ChatMessage:
    """Helper function to create a chat message."""
    return ChatMessage(role, content)