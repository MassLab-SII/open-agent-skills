import asyncio
import json
from skills.github.utils import GitHubTools

async def main():
    print("Connecting to MCP Server...")
    try:
        async with GitHubTools() as gh:
            print("Connected. Listing tools...")
            # Access the underlying session
            result = await gh.mcp_server.session.list_tools()
            
            tools = []
            if result and hasattr(result, 'tools'):
                 tools = result.tools
            else:
                 print(f"Unexpected result format: {result}")
                 return

            print(f"Found {len(tools)} tools:")
            for tool in tools:
                print(f"- {tool.name}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
