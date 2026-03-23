from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Production server URL
url = 'https://invisible-lime-spider.fastmcp.app'

# Get access token from .env
access_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYXN0bWNwLXVzZXIiLCJpc3MiOiJodHRwczovL2Zhc3RtY3AuZXhhbXBsZS5jb20iLCJpYXQiOjE3NzQyNTMwMTQsImV4cCI6MTc3NDI1NjYxNCwiYXVkIjoiaW52aXNpYmxlLWxpbWUtc3BpZGVyIn0.JnwFNq-9ok83TVbD414ECb9MUcGqXDoaPBUfF-EsQv_L6_ninHRuoRL0NUmGf43l4ylKvhptxCb0VDDWUvznasWpx4IwekfNjmvk-1tABiQE94V1rIv_atoFq8Ll2UEpEWzHXvvw4jiiVxPjq5iTFp-4eQbPADi6-B3eFTf017vD8RvdvtDRi4Bd9aFORdqA8LRI3akyDAabGCD-VQzrIeDDLReoUDW-aJE0kE4Yb5oGpcB_AsWI4Cb-24jvpDzn1YyMC5Tqof89nfIWu22p-2kdoFjOC3KI-HoHswfKrXqCQ8igNS10hEiIjK_msgeVyh7XF4MsKaWx3T2HdJgQCQ"

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