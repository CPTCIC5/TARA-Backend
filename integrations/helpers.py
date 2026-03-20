from sqlalchemy.orm import Session
from fastapi import Depends
from db.models import get_db, Channel
# Function to get the channel object using the user id and channel type
def get_channel(channel_type_num:int , user_id:int ,db: Session = Depends(get_db)):
    return db.query(Channel).filter(Channel.user_id== user_id, Channel.channel_type== channel_type_num).first()

# Function to create a new channel object 
def create_channel(channel_type_num:int , user_id:int ,db: Session = Depends(get_db)):
    new_channel = Channel(user_id=user_id, channel_type=channel_type_num)
    db.add(new_channel)
    try:
        db.commit()
        db.refresh(new_channel)
    except Exception as e:
        db.rollback()
        raise (str(e), "Error in creating channel object")
    return new_channel

# Function which get's the channel object as input and checks for valid credentials / refresh credentials
def refresh_credentials(channel):
    print("refresh function called")

    
