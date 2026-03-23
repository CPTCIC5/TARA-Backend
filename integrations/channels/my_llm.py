from openai import OpenAI
from dotenv import load_dotenv
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from db.models import SessionLocal, User

load_dotenv()

# Ngrok URL for testing
url = 'https://monitor-happy-mole.ngrok-free.app'

client = OpenAI()

def get_or_create_conversation(user_id: int) -> str:
    """Get existing conversation ID for user from database or create new one"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # If user has no conversation (formerly thread), create one
        if not user.thread_id:
            # Replaces client.threads.create()
            conversation = client.conversations.create()
            user.thread_id = conversation.id
            db.commit()
        
        return user.thread_id
    finally:
        db.close()

def clear_conversation(user_id: int):
    """Clear conversation for user (start fresh)"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.thread_id:
            user.thread_id = None
            db.commit()
    finally:
        db.close()

def ask_llm(msg: str, user_id: int):
    conv_id = get_or_create_conversation(user_id)
    
    # Replaces client.beta.threads.runs.create()
    resp = client.responses.create(
        model="gpt-4o",
        conversation=conv_id,  # Parameter is now 'conversation'
        store=True,            # Must be True to persist messages in the conversation
        instructions=f"""You're an assistant like Jarvis having access to multiple tools and systems via MCP.

CRITICAL: The authenticated user's database ID is {user_id}. 
You MUST pass db_user_id={user_id} to EVERY tool call you make.""",
        tools=[
            {
                "type": "mcp",
                "server_label": "google_workspace_server",
                "server_url": f"{url}/mcp/",
                "require_approval": "never",
            },
        ],
        input=msg
    )
    # Responses API provides output_text directly in the response object
    return resp.output_text

if __name__=="__main__":
    user_id = int(input("Enter your user ID: "))
    print("Chat started! Type 'clear' to reset conversation, 'quit' to exit.\n")
    
    while True:
        ask = input("You: ")
        if ask.lower() == 'quit':
            break
        if ask.lower() == 'clear':
            clear_conversation(user_id)
            print("Conversation cleared!\n")
            continue
        
        response = ask_llm(ask, user_id)
        print(f"\nAssistant: {response}\n")