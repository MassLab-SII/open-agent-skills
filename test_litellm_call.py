"""
Test LiteLLM acompletion calls
This script independently tests whether litellm.acompletion works properly
"""

import asyncio
import litellm
from typing import Dict, List, Any
from dotenv import load_dotenv
import os
import json
import httpx

load_dotenv(".mcp_env")
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")




async def test_litellm_call():
    """Test basic LiteLLM call"""
    
    # Example messages
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "Hello! are you really happy?"
        }
    ]
    
    # Example tool definition
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city name"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    # Build completion parameters (similar to original code)
    completion_kwargs = {
        "model": "openai/gpt-5",
        "api_key": api_key,
        "base_url": base_url,
        "messages": messages,
    }
    
    # ⚠️ Temporarily not adding tools, test basic call first
    completion_kwargs["tools"] = tools
    completion_kwargs["tool_choice"] = "auto"
    
    # print("⚠️  Note: Temporarily disabling tool calls, testing basic API first")
    
    print("=" * 60)
    print("Test Configuration:")
    print(f"Model: {completion_kwargs['model']}")
    print(f"Number of messages: {len(messages)}")
    print(f"Number of tools: {len(tools)}")
    print("=" * 60)
    
    try:
        print("\nStarting litellm.acompletion call...")
        print(f"Debug info:")
        print(f"  - Model: {completion_kwargs['model']}")
        print(f"  - Base URL: {completion_kwargs.get('base_url', 'default')}")
        print(f"  - Using tools: {'tools' in completion_kwargs}")
        
        # Use asyncio.wait_for to add timeout (similar to original code)
        response = await asyncio.wait_for(
            litellm.acompletion(**completion_kwargs),
            timeout=30  # 30 second timeout
        )
        
        print("✓ Call successful!")
        print("\nResponse info:")
        print(f"- Response type: {type(response)}")
        print(f"- Model: {response.model if hasattr(response, 'model') else 'N/A'}")
        
        # Display token usage
        if hasattr(response, 'usage') and response.usage:
            print(f"- Input tokens: {response.usage.prompt_tokens}")
            print(f"- Output tokens: {response.usage.completion_tokens}")
            print(f"- Total tokens: {response.usage.total_tokens}")
            
            # Check reasoning tokens (if available)
            if hasattr(response.usage, 'completion_tokens_details'):
                details = response.usage.completion_tokens_details
                if hasattr(details, 'reasoning_tokens') and details.reasoning_tokens:
                    print(f"- Reasoning tokens: {details.reasoning_tokens}")
        
        # Display response content
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message'):
                message = choice.message
                print(f"\nResponse content:")
                if hasattr(message, 'content') and message.content:
                    print(f"  Content: {message.content}")
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    print(f"  Tool calls: {len(message.tool_calls)} call(s)")
                    for i, tool_call in enumerate(message.tool_calls):
                        print(f"    [{i+1}] {tool_call.function.name}")
        
        return response
        
    except asyncio.TimeoutError:
        print("✗ Call timed out!")
        raise
    except Exception as e:
        print(f"✗ Call failed: {type(e).__name__}")
        print(f"  Error message: {str(e)}")
        raise

async def test_raw_api():
    """Test API raw response directly"""
    print("\n" + "=" * 60)
    print("Test: Direct API call to view raw response")
    print("=" * 60)
    
    import httpx
    
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-5",
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }
    
    print(f"\nRequest info:")
    print(f"  URL: {url}")
    print(f"  Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"\nResponse status code: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"\nResponse JSON:")
                print(json.dumps(response_json, indent=2, ensure_ascii=False))
                
                # Check if choices field exists
                if "choices" in response_json:
                    print("\n✓ Response contains choices field")
                else:
                    print("\n✗ Response missing choices field!")
                    print(f"Actual fields: {list(response_json.keys())}")
                    
            except json.JSONDecodeError:
                print(f"\nResponse text (non-JSON):")
                print(response.text)
                
    except Exception as e:
        print(f"\n✗ Request failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_without_tools():
    """Test simple call without tools"""
    
    messages = [
        {
            "role": "user",
            "content": "Say 'Hello World' in Chinese."
        }
    ]
    
    completion_kwargs = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
    }
    
    print("\n" + "=" * 60)
    print("Test call without tools:")
    print("=" * 60)
    
    try:
        response = await asyncio.wait_for(
            litellm.acompletion(**completion_kwargs),
            timeout=30
        )
        
        print("✓ Call successful!")
        
        if hasattr(response, 'choices') and response.choices:
            message = response.choices[0].message
            if hasattr(message, 'content'):
                print(f"\nResponse: {message.content}")
        
        return response
        
    except Exception as e:
        print(f"✗ Call failed: {str(e)}")
        raise


async def test_concurrent_calls():
    """Demonstrate concurrent calls - showing non-blocking advantages"""
    import time
    
    print("\n" + "=" * 60)
    print("Demo: Concurrent API calls (non-blocking)")
    print("=" * 60)
    
    # Create 3 different requests
    async def call_api(task_id: int, question: str):
        print(f"[Task {task_id}] Starting API call...")
        start_time = time.time()
        
        messages = [{"role": "user", "content": question}]
        completion_kwargs = {
            "model": "openai/gpt-5",
            "api_key": api_key,
            "base_url": base_url,
            "messages": messages,
        }
        
        try:
            response = await asyncio.wait_for(
                litellm.acompletion(**completion_kwargs),
                timeout=60
            )
            elapsed = time.time() - start_time
            
            content = response.choices[0].message.content if response.choices else "No content"
            print(f"[Task {task_id}] ✓ Completed! Time: {elapsed:.2f}s")
            print(f"[Task {task_id}] Reply: {content[:50]}...")
            return response
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"[Task {task_id}] ✗ Failed! Time: {elapsed:.2f}s, Error: {str(e)}")
            raise
    
    # Method 1: Sequential execution (blocking)
    print("\n【Method 1: Sequential execution - one by one】")
    start = time.time()
    await call_api(1, "What is 1+1?")
    await call_api(2, "What is Python?")
    await call_api(3, "Hello")
    sequential_time = time.time() - start
    print(f"\nSequential execution total time: {sequential_time:.2f}s")
    
    # Method 2: Concurrent execution (non-blocking)
    print("\n【Method 2: Concurrent execution - simultaneous】")
    start = time.time()
    await asyncio.gather(
        call_api(4, "What is 1+1?"),
        call_api(5, "What is Python?"),
        call_api(6, "Hello")
    )
    concurrent_time = time.time() - start
    print(f"\nConcurrent execution total time: {concurrent_time:.2f}s")
    
    # Comparison
    print("\n" + "=" * 60)
    print(f"Performance comparison:")
    print(f"  Sequential: {sequential_time:.2f}s")
    print(f"  Concurrent: {concurrent_time:.2f}s")
    print(f"  Speedup: {(sequential_time / concurrent_time):.2f}x")
    print("=" * 60)


async def main():
    """Main function"""
    print("LiteLLM acompletion Test Script")
    print("=" * 60)
    print("\nNotes:")
    print("1. Make sure litellm is installed: pip install litellm")
    print("2. API key must be set (via environment variable or in code)")
    print("3. Network connection required to access API")
    print("\n")
    
    try:
        # Test 0: View raw API response (for debugging)
        # await test_raw_api()
        
        # Test 1: Call with tools
        # await test_litellm_call()
        
        # Test 2: Concurrent call demo (showing non-blocking advantages)
        await test_concurrent_calls()
        
        print("\n" + "=" * 60)
        print("All tests completed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"Test failed: {str(e)}")
        print("=" * 60)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run async main function
    asyncio.run(main())

