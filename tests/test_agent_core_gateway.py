#!/usr/bin/env python3
"""
Test script for Agent Core Gateway MCP server functionality.

This script tests the connection to the Tavily MCP gateway by:
1. Fetching an access token from AWS Cognito
2. Using the token to list available tools from the MCP server
3. Optionally testing tool execution

Usage:
    python tests/test_agent_core_gateway.py
    
Environment variables required:
    COGNITO_CLIENT_ID
    COGNITO_CLIENT_SECRET
    COGNITO_USER_POOL_DOMAIN
    TAVILY_MCP_URL
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fetch_access_token(client_id, client_secret, token_url):
    """
    Fetch access token from AWS Cognito using client credentials flow.
    
    Args:
        client_id (str): Cognito client ID
        client_secret (str): Cognito client secret
        token_url (str): Cognito token endpoint URL
        
    Returns:
        str: Access token
    """
    print(f"Fetching access token from: {token_url}")
    
    response = requests.post(
        token_url,
        data=f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}",
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    if response.status_code == 200:
        token_data = response.json()
        print("✅ Successfully fetched access token")
        return token_data['access_token']
    else:
        print(f"❌ Failed to fetch access token. Status: {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception(f"Token fetch failed: {response.status_code}")

def list_tools(gateway_url, access_token):
    """
    List and display available tools from the MCP server in detail.
    
    Args:
        gateway_url (str): MCP gateway URL
        access_token (str): Bearer token for authentication
        
    Returns:
        dict: JSON response with available tools
    """
    print(f"Listing tools from: {gateway_url}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "jsonrpc": "2.0",
        "id": "list-tools-request",
        "method": "tools/list"
    }

    response = requests.post(gateway_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        tools_response = response.json()
        print("✅ Successfully listed tools")
        
        # Display tools in a formatted way
        if tools_response.get('result', {}).get('tools'):
            available_tools = tools_response['result']['tools']
            
            print(f"\n🔧 AVAILABLE TOOLS ({len(available_tools)} total)")
            print("=" * 80)
            
            for i, tool in enumerate(available_tools, 1):
                name = tool.get('name', 'Unknown')
                description = tool.get('description', 'No description available')
                input_schema = tool.get('inputSchema', {})
                required = input_schema.get('required', [])
                properties = input_schema.get('properties', {})
                
                print(f"\n{i}. {name}")
                print(f"   📝 Description: {description}")
                
                if required:
                    print(f"   ✅ Required parameters: {', '.join(required)}")
                else:
                    print(f"   ✅ Required parameters: None")
                
                if properties:
                    optional_params = [p for p in properties.keys() if p not in required]
                    if optional_params:
                        print(f"   🔧 Optional parameters: {', '.join(optional_params)}")
                    
                    # Show parameter details
                    print(f"   📋 Parameter details:")
                    for param_name, param_info in properties.items():
                        param_type = param_info.get('type', 'unknown')
                        param_desc = param_info.get('description', 'No description')
                        required_marker = "🔴" if param_name in required else "🟡"
                        print(f"      {required_marker} {param_name} ({param_type}): {param_desc}")
                
                print("-" * 60)
        else:
            print("⚠️  No tools found in response")
        
        return tools_response
    else:
        print(f"❌ Failed to list tools. Status: {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception(f"Tools list failed: {response.status_code}")

def get_tool_parameters(tool_info):
    """
    Extract appropriate parameters for a tool based on its schema.
    
    Args:
        tool_info (dict): Tool information from the MCP server
        
    Returns:
        dict: Appropriate parameters for the tool
    """
    tool_name = tool_info.get('name', '')
    input_schema = tool_info.get('inputSchema', {})
    properties = input_schema.get('properties', {})
    required = input_schema.get('required', [])
    
    print(f"Tool '{tool_name}' schema:")
    print(f"  Required fields: {required}")
    print(f"  Available properties: {list(properties.keys())}")
    
    # Default parameters for different tool types
    if 'tavily' in tool_name.lower():
        if 'extract' in tool_name.lower():
            # TavilySearchExtract requires URLs
            return {
                "urls": ["https://example.com"],
                "query": "test query"
            }
        elif 'search' in tool_name.lower():
            # TavilySearch requires query
            return {
                "query": "What is the weather today?"
            }
    
    # Generic fallback - try to provide common parameters
    params = {}
    
    # Common parameter mappings
    param_mappings = {
        'query': "What is the weather today?",
        'q': "What is the weather today?",
        'search_query': "What is the weather today?",
        'urls': ["https://example.com"],
        'url': "https://example.com",
        'text': "sample text",
        'content': "sample content"
    }
    
    # Fill in required parameters
    for param in required:
        if param in param_mappings:
            params[param] = param_mappings[param]
        else:
            # Try to infer from property type
            prop_info = properties.get(param, {})
            prop_type = prop_info.get('type', 'string')
            
            if prop_type == 'string':
                params[param] = f"sample_{param}"
            elif prop_type == 'array':
                params[param] = [f"sample_{param}"]
            elif prop_type == 'boolean':
                params[param] = True
            elif prop_type == 'number' or prop_type == 'integer':
                params[param] = 1
            else:
                params[param] = f"sample_{param}"
    
    return params

def test_tool_execution(gateway_url, access_token, tool_info):
    """
    Test executing a specific tool with appropriate parameters.
    
    Args:
        gateway_url (str): MCP gateway URL
        access_token (str): Bearer token for authentication
        tool_info (dict): Tool information from the MCP server
        
    Returns:
        dict: JSON response from tool execution
    """
    tool_name = tool_info.get('name', 'unknown')
    print(f"Testing tool execution: {tool_name}")
    
    # Get appropriate parameters for this tool
    tool_params = get_tool_parameters(tool_info)
    print(f"Using parameters: {tool_params}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "jsonrpc": "2.0",
        "id": "tool-execution-request",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": tool_params
        }
    }

    response = requests.post(gateway_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('result', {}).get('isError'):
            print("⚠️  Tool executed but returned an error")
        else:
            print("✅ Successfully executed tool")
        return result
    else:
        print(f"❌ Failed to execute tool. Status: {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception(f"Tool execution failed: {response.status_code}")

def inspect_tools(tools_list):
    """
    Inspect and display information about available tools.
    
    Args:
        tools_list (list): List of tools from the MCP server
    """
    print(f"\n📋 Available Tools ({len(tools_list)} total):")
    print("=" * 50)
    
    for i, tool in enumerate(tools_list, 1):
        name = tool.get('name', 'Unknown')
        description = tool.get('description', 'No description')
        input_schema = tool.get('inputSchema', {})
        required = input_schema.get('required', [])
        properties = input_schema.get('properties', {})
        
        print(f"{i}. {name}")
        print(f"   Description: {description}")
        print(f"   Required parameters: {required}")
        print(f"   Available parameters: {list(properties.keys())}")
        print()

def main():
    """Main test function."""
    print("🚀 Starting Agent Core Gateway MCP Server Test")
    print("=" * 50)
    
    # Get configuration from environment variables
    client_id = os.getenv("COGNITO_CLIENT_ID")
    client_secret = os.getenv("COGNITO_CLIENT_SECRET")
    user_pool_domain = os.getenv("COGNITO_USER_POOL_DOMAIN")
    gateway_url = os.getenv("TAVILY_MCP_URL")
    
    # Validate environment variables
    if not all([client_id, client_secret, user_pool_domain, gateway_url]):
        print("❌ Missing required environment variables:")
        print(f"  COGNITO_CLIENT_ID: {'✅' if client_id else '❌'}")
        print(f"  COGNITO_CLIENT_SECRET: {'✅' if client_secret else '❌'}")
        print(f"  COGNITO_USER_POOL_DOMAIN: {'✅' if user_pool_domain else '❌'}")
        print(f"  TAVILY_MCP_URL: {'✅' if gateway_url else '❌'}")
        return
    
    # Construct token URL
    token_url = f"{user_pool_domain.rstrip('/')}/oauth2/token"
    
    # Ensure gateway URL has /mcp suffix
    if not gateway_url.endswith('/mcp'):
        gateway_url = f"{gateway_url.rstrip('/')}/mcp"
    
    print(f"Configuration:")
    print(f"  Token URL: {token_url}")
    print(f"  Gateway URL: {gateway_url}")
    print()
    
    try:
        # Step 1: Fetch access token
        print("Step 1: Fetching access token...")
        access_token = fetch_access_token(client_id, client_secret, token_url)
        print(f"Token (first 20 chars): {access_token[:20]}...")
        print()
        
        # Step 2: List available tools
        print("Step 2: Listing available tools...")
        tools_response = list_tools(gateway_url, access_token)
        print("Tools response:")
        print(json.dumps(tools_response, indent=2))
        print()
        
        # Step 3: Inspect tools and test execution
        if tools_response.get('result', {}).get('tools'):
            available_tools = tools_response['result']['tools']
            if available_tools:
                # Display tool information
                inspect_tools(available_tools)
                
                # Test the first tool
                first_tool = available_tools[0]
                print(f"Step 3: Testing tool execution with '{first_tool.get('name')}'...")
                execution_response = test_tool_execution(gateway_url, access_token, first_tool)
                print("Tool execution response:")
                print(json.dumps(execution_response, indent=2))
                
                # If there are multiple tools, offer to test more
                if len(available_tools) > 1:
                    print(f"\n🔧 Additional tools available for testing:")
                    for i, tool in enumerate(available_tools[1:], 2):
                        print(f"  {i}. {tool.get('name')}")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
