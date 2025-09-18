#!/usr/bin/env python3

import asyncio
import os
from emergentintegrations.llm.chat import LlmChat, UserMessage

async def test_llm():
    client = LlmChat(api_key=os.environ.get('EMERGENT_LLM_KEY'))
    client = client.with_model('openai', 'gpt-4o-mini')
    
    msg = UserMessage(text='Hello, how are you?')
    resp = await client.send_message(msg)
    
    print("Response type:", type(resp))
    print("Response attributes:", dir(resp))
    print("Response:", resp)
    
    if hasattr(resp, 'content'):
        print("Response content:", resp.content)
    elif hasattr(resp, 'text'):
        print("Response text:", resp.text)
    elif hasattr(resp, 'message'):
        print("Response message:", resp.message)

if __name__ == "__main__":
    asyncio.run(test_llm())