import asyncio
from google import genai
from google.genai import types

async def main():
    client = genai.Client(api_key="mock")
    print("Client created")
    print(dir(client))
    print(dir(client.aio.models))
    print(dir(client.aio.chats))
    
    config = types.GenerateContentConfig(
        temperature=0.7,
        system_instruction="You are a helpful assistant",
    )
    print("Config created:", config)

if __name__ == "__main__":
    asyncio.run(main())
