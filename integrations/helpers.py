import json
from sqlalchemy.orm import Session
from fastapi import Depends
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from db.models import get_db, Channel, APICredentials

# Function to get the channel object using the user id and channel type
def get_channel(channel_type_num: int, user_id: int, db: Session):
    return db.query(Channel).filter(Channel.user_id == user_id, Channel.channel_type == channel_type_num).first()

# Function to create a new channel object with credentials
def create_channel(channel_type_num: int, user_id: int, db: Session):
    # Create API credentials entry first
    api_creds = APICredentials()
    db.add(api_creds)
    db.flush()  # Get the ID without committing
    
    # Create channel linked to credentials
    new_channel = Channel(
        user_id=user_id, 
        channel_type=channel_type_num,
        credentials_id=api_creds.id
    )
    db.add(new_channel)
    
    try:
        db.commit()
        db.refresh(new_channel)
        db.refresh(api_creds)
    except Exception as e:
        db.rollback()
        raise Exception(f"Error in creating channel object: {str(e)}")
    
    return new_channel

class RefreshException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f'RefreshException: {self.message}'

# Function to convert Google OAuth credentials to database format
def credentials_to_db(creds: Credentials, channel: Channel, db: Session):
    """Store Google OAuth credentials in the database"""
    try:
        if not channel.credentials:
            # Create new credentials if they don't exist
            api_creds = APICredentials()
            db.add(api_creds)
            db.flush()
            channel.credentials_id = api_creds.id
            db.flush()
            db.refresh(channel)
        
        # Store credentials in key fields
        channel.credentials.key_1 = creds.token  # access_token
        channel.credentials.key_2 = creds.refresh_token  # refresh_token
        channel.credentials.key_3 = creds.token_uri  # token_uri
        channel.credentials.key_4 = creds.client_id  # client_id
        channel.credentials.key_5 = creds.client_secret  # client_secret
        channel.credentials.key_6 = json.dumps(creds.scopes) if creds.scopes else None  # scopes
        
        db.commit()
        db.refresh(channel)
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to store credentials: {str(e)}")

# Function to convert database credentials to Google OAuth credentials
def credentials_from_db(channel: Channel) -> Credentials:
    """Load Google OAuth credentials from the database"""
    if not channel.credentials:
        raise RefreshException("No credentials found for this channel")
    
    creds_data = channel.credentials
    
    if not creds_data.key_1:  # No access token
        raise RefreshException("Channel credentials are not initialized")
    
    # Parse scopes safely
    try:
        scopes = json.loads(creds_data.key_6) if creds_data.key_6 else []
    except (json.JSONDecodeError, TypeError):
        scopes = []
    
    creds = Credentials(
        token=creds_data.key_1,  # access_token
        refresh_token=creds_data.key_2,  # refresh_token
        token_uri=creds_data.key_3,  # token_uri
        client_id=creds_data.key_4,  # client_id
        client_secret=creds_data.key_5,  # client_secret
        scopes=scopes
    )
    
    return creds

# Function which checks if credentials are valid
def check_credentials(channel: Channel) -> bool:
    """Check if channel has valid credentials"""
    try:
        if not channel.credentials:
            return False
        
        creds = credentials_from_db(channel)
        return creds.valid
    except Exception:
        return False

# Function which refreshes credentials if expired
def refresh_credentials(channel: Channel, db: Session):
    """Refresh expired credentials and update in database"""
    try:
        creds = credentials_from_db(channel)
        
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Update credentials in database
                    credentials_to_db(creds, channel, db)
                except Exception as refresh_error:
                    # Refresh failed - clear invalid credentials so user can re-authenticate
                    if channel.credentials:
                        db.delete(channel.credentials)
                    db.delete(channel)
                    db.commit()
                    raise RefreshException(f"Credentials refresh failed and channel cleared: {str(refresh_error)}")
            else:
                # No refresh token or credentials not refreshable - clear channel
                if channel.credentials:
                    db.delete(channel.credentials)
                db.delete(channel)
                db.commit()
                raise RefreshException("Credentials cannot be refreshed - channel cleared, re-authentication required")
        
        return creds
    except RefreshException:
        # Re-raise RefreshException as-is
        raise
    except Exception as e:
        # Unexpected error - clear channel to be safe
        try:
            if channel.credentials:
                db.delete(channel.credentials)
            db.delete(channel)
            db.commit()
        except:
            db.rollback()
        raise RefreshException(f"Failed to refresh credentials and channel cleared: {str(e)}")