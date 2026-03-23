from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()


# Ngrok URL for testing
url = 'https://monitor-happy-mole.ngrok-free.app'

client = OpenAI()

def ask_llm(msg: str):
    resp = client.responses.create(
        model="gpt-5",
        instructions="You're an assistant like Jarvis having access to multiple tools and systems via MCP refer it and use ur common sense to cater the end-user",
        tools=[
            {
                "type": "mcp",
                "server_label": "invisible-lime-spider",
                "server_url": f"{url}/mcp/",
                "require_approval": "never",
            },
        ],
        input=msg
    )
    return resp.output_text

if __name__=="__main__":
    ask=input("Input")
    print(ask_llm(ask))