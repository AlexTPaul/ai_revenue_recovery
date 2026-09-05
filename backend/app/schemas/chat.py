from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ChatMessageRequest(BaseModel):
    promise_id: str
    message: str
    language: Optional[str] = "hinglish"  # "english" | "hinglish"



class ParsedCommitment(BaseModel):
    has_commitment: bool
    is_ambiguous: bool
    promised_date: Optional[date] = None
    refused: bool = False
    confidence: float = 1.0
    clarification_message: Optional[str] = None
    confirmation_message: Optional[str] = None


class ChatMessageResponse(BaseModel):
    status: str
    agent_reply: str
    extracted_data: ParsedCommitment
    promise_status: str
    payment_link: Optional[str] = None


class ConversationEntry(BaseModel):
    id: str
    promise_id: str
    sender: str
    message: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    promise_id: str
    customer_name: str
    customer_phone: str
    amount: float
    promised_date: Optional[date]
    status: str
    payment_link: Optional[str]
    messages: List[ConversationEntry]
