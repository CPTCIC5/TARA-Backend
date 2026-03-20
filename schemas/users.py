from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import IntEnum

class UserBase(BaseModel):
    email: EmailStr
    name: str
    profile_picture: Optional[str] = None

class UserCreate(UserBase):
    google_id: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    google_id: str
    is_active: bool
    joined_at: datetime
    name: Optional[str] = None
    profile_picture: Optional[str] = None
    
    class Config:
        from_attributes = True

class GoogleTokenRequest(BaseModel):
    token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Integration schemas
class IntegrationsEnum(IntEnum):
    GMAIL = 1
    UBER = 2
    WHATSAPP = 3
    GOOGLE_MEET = 4
    GOOGLE_CALENDAR = 5
    GOOGLE_DOCS = 6
    SLACK = 7

class ChannelBase(BaseModel):
    channel_type: IntegrationsEnum

class ChannelCreate(ChannelBase):
    user_id: int
    credentials_id: Optional[int] = None

class ChannelResponse(ChannelBase):
    id: int
    user_id: int
    credentials_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class APICredentialsBase(BaseModel):
    key_1: Optional[str] = None
    key_2: Optional[str] = None
    key_3: Optional[str] = None
    key_4: Optional[str] = None
    key_5: Optional[str] = None
    key_6: Optional[str] = None

class APICredentialsCreate(APICredentialsBase):
    pass

class APICredentialsResponse(APICredentialsBase):
    id: int
    
    class Config:
        from_attributes = True

# Update UserResponse to include channels
class UserResponseWithChannels(BaseModel):
    id: int
    email: EmailStr
    google_id: str
    is_active: bool
    joined_at: datetime
    name: Optional[str] = None
    profile_picture: Optional[str] = None
    channels: List[ChannelResponse] = []
    
    class Config:
        from_attributes = True