from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Production server URL
url = 'https://invisible-lime-spider.fastmcp.app'

# Get access token from .env
access_token = os.getenv('MCP_ACCESS_TOKEN')

if not access_token:
    print("❌ Error: MCP_ACCESS_TOKEN not found in .env file")
    print("\nRun the server first to generate a token:")
    print("  python integrations/channels/my_server.py")
    print("\nThen copy the token to your .env file:")
    print("  MCP_ACCESS_TOKEN=your_token_here")
    exit(1)

client = OpenAI()

print(f"🚀 Connecting to MCP server at: {url}")
print("📧 Testing Gmail integration with OpenAI Responses API...\n")

resp = client.responses.create(
    model="gpt-4.1",
    tools=[
        {
            "type": "mcp",
            "server_label": "invisible-lime-spider",
            "server_url": f"{url}/mcp/",
            "require_approval": "never",
            "headers": {
                "Authorization": f"Bearer {access_token}"
            }
        },
    ],
    input="List my recent Gmail messages",
)

print("✅ Success!")
print(f"\n{resp.output_text}")