from openai import OpenAI
from dotenv import load_dotenv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from db.models import SessionLocal, User

load_dotenv()
url = 'https://monitor-happy-mole.ngrok-free.app'
client = OpenAI()

def get_or_create_conversation(user_id: int) -> str:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if not user.thread_id:
            conversation = client.conversations.create()
            user.thread_id = conversation.id
            db.commit()
        
        return user.thread_id
    finally:
        db.close()

def clear_conversation(user_id: int):
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
    
    resp = client.responses.create(
        model="gpt-5.4",
        conversation=conv_id,
        store=True,
        reasoning={"effort": "low"},
        instructions=f"""You're Jarvis. A general purpose smart-assistant

Pass db_user_id={user_id} to all tools. Complete tasks fully.""",
        tools=[{
            "type": "mcp",
            "server_label": "google_workspace_server",
            "server_url": f"{url}/mcp/",
            "require_approval": "never",
        },
        {"type": "web_search"}],
        input=msg
    )
    return resp.output_text

if __name__=="__main__":
    user_id = int(input("Enter your user ID: "))
    print("Chat started! Type 'clear' to reset, 'quit' to exit.\n")
    
    while True:
        ask = input("You: ")
        if ask.lower() == 'quit':
            break
        if ask.lower() == 'clear':
            clear_conversation(user_id)
            print("Conversation cleared!\n")
            continue
        
        response = ask_llm(ask, user_id)
        print(f"\nJarvis: {response}\n")
