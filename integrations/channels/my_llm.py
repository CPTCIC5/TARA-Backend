from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Ngrok URL for testing
url = 'https://monitor-happy-mole.ngrok-free.app'

client = OpenAI()

def ask_llm(msg: str, user_id: int):
    resp = client.responses.create(
        model="gpt-5",
        instructions=f"""You're an assistant like Jarvis having access to multiple tools and systems via MCP.

Example tool calls:
- gmail_list_messages(db_user_id={user_id}, max_results=10)
- calendar_list_events(db_user_id={user_id})
- drive_list_files(db_user_id={user_id})

Always include db_user_id={user_id} in every single tool invocation.""",
        tools=[
            {
                "type": "mcp",
                "server_label": "google_workspace_server",
                "server_url": f"{url}/mcp/",
                "require_approval": "never",
            },
            {"type": "web_search"},
        ],
        input=msg
    )
    return resp.output_text

if __name__=="__main__":
    user_id = int(input("Enter your user ID: "))
    ask = input("What would you like to do? ")
    print(ask_llm(ask, user_id))