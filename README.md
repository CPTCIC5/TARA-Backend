fastmcp dev inspector integrations/channels/my_server.py:mcp

python integrations/channels/my_server.py
ngrok http --domain=monitor-happy-mole.ngrok-free.app 8000

uvicorn integrations.channels.voice_server:app --reload --port 3000