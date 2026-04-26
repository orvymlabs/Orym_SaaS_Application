from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class Bot(BaseModel):
    id: int
    user_id: int
    mode: str
    status: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class BotResponse(Bot): # Inherit from Bot or define fields explicitly
    pass

class BotModeUpdate(BaseModel): # Added BotModeUpdate class
    mode: str

class BotStatusUpdate(BaseModel): # Added BotStatusUpdate class
    status: bool

class BotCreate(BaseModel):
    mode: str
    status: bool = True

class BotSettings(BaseModel):
    bot_id: int
    greeting_message: Optional[str] = None
    custom_responses: Optional[dict] = None
    custom_products: Optional[Any] = None

class BotSettingsUpdate(BaseModel):
    prompt: Optional[str] = None
    model_name: Optional[str] = None  # Provider: openai, gemini, openrouter, qwen
    specific_model_name: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[int] = None  # 0-100 stored as int, converted to float for AI
    language: Optional[str] = None
    templates: Optional[Dict[str, str]] = None
    template_enabled: Optional[bool] = None
    template_statuses: Optional[Dict[str, bool]] = None # Added for individual template statuses
    custom_responses: Optional[Dict[str, str]] = None # Added custom_responses field
    custom_products: Optional[Any] = None

class SettingsResponse(BaseModel): # Added SettingsResponse class
    id: int
    bot_id: int
    prompt: Optional[str] = None
    model_name: Optional[str] = None
    specific_model_name: Optional[str] = None
    temperature: Optional[int] = None
    language: Optional[str] = None
    templates: Optional[Dict[str, str]] = None
    template_enabled: Optional[bool] = None
    custom_products: Optional[Any] = None
    has_api_key: bool # Added has_api_key field

class TestChatRequest(BaseModel): # Added TestChatRequest class
    message: str

class TestChatResponse(BaseModel): # Added TestChatResponse class
    reply: str
    mode: str
    bot_id: int

