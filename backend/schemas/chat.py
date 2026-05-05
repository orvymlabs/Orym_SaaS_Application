from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageOut(BaseModel):
    id: int
    bot_id: int
    sender: str
    phone_number: str
    message: Optional[str]
    timestamp: Optional[datetime]
    seen: bool = False

    class Config:
        from_attributes = True


class LeadOut(BaseModel):
    id: int
    bot_id: int
    phone: str
    name: Optional[str]
    last_message: Optional[str]
    message_count: int = 0
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    bot_id: int
    user_id: int
    name: str
    phone: str
    address: str
    product_name: str
    quantity: int
    source: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
