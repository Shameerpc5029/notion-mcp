"""
Notion MCP Server - A Model Context Protocol server for Notion API operations
"""

import asyncio
import json
import logging
import sys
from typing import Dict, List, Optional, Any, Sequence
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
import requests
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

class NotionAPIError(Exception):
    """Custom exception for Notion API errors"""
    pass

class NotionAuthError(Exception):
    """Custom exception for Notion authentication errors"""
    pass

def get_connection_credentials(id: str, providerConfigKey: str) -> Dict[str, Any]:
    """Get credentials from Nango"""
    base_url = os.environ.get("NANGO_BASE_URL")
    secret_key = os.environ.get("NANGO_SECRET_KEY")
    
    if not base_url or not secret_key:
        raise NotionAuthError("NANGO_BASE_URL and NANGO_SECRET_KEY environment variables must be set")
    
    url = f"{base_url}/connection/{id}"
    params = {
        "provider_config_key": providerConfigKey,
        "refresh_token": "true",
    }
    headers = {"Authorization": f"Bearer {secret_key}"}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    return response.json()

class NotionClient:
    """Notion API client for MCP server"""
    
    def __init__(self, auth_token: Optional[str] = None, notion_version: str = "2022-06-28", 
                nango_connection_id: Optional[str] = None, nango_provider_config_key: Optional[str] = None):
        self.notion_version = notion_version
        self.base_url = "https://api.notion.com/v1"
        
        # Use provided values or fall back to environment variables
        self.nango_connection_id = nango_connection_id or os.environ.get("NANGO_CONNECTION_ID")
        self.nango_provider_config_key = nango_provider_config_key or os.environ.get("NANGO_INTEGRATION_ID")
        
        # Initialize auth token
        if auth_token:
            self.auth_token = auth_token
        elif self.nango_connection_id and self.nango_provider_config_key:
            self.auth_token = self._get_nango_token()
        else:
            raise NotionAuthError("Either auth_token or both nango_connection_id and nango_provider_config_key must be provided")
        
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Notion-Version": notion_version,
            "Content-Type": "application/json"
        }
    
    def _get_nango_token(self) -> str:
        """Get access token from Nango"""
        try:
            credentials = get_connection_credentials(self.nango_connection_id, self.nango_provider_config_key)
            
            if 'credentials' in credentials:
                return credentials['credentials'].get('access_token')
            elif 'access_token' in credentials:
                return credentials['access_token']
            else:
                raise NotionAuthError("No access token found in Nango credentials response")
                
        except Exception as e:
            raise NotionAuthError(f"Failed to get credentials from Nango: {str(e)}")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Notion API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if method.upper() == "GET":
                    response = requests.get(url, headers=self.headers, params=params)
                elif method.upper() == "POST":
                    response = requests.post(url, headers=self.headers, json=data)
                elif method.upper() == "PATCH":
                    response = requests.patch(url, headers=self.headers, json=data)
                elif method.upper() == "DELETE":
                    response = requests.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 1))
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json() if response.content else {}
                
            except requests.exceptions.RequestException as e:
                if retry_count == max_retries - 1:
                    raise NotionAPIError(f"API request failed after {max_retries} retries: {str(e)}")
                retry_count += 1
                time.sleep(1)
    
    # Core API methods
    def get_database(self, database_id: str) -> Dict:
        """Retrieve a database"""
        return self._make_request("GET", f"databases/{database_id}")
    
    def query_database(self, database_id: str, filter_criteria: Optional[Dict] = None, 
                    sorts: Optional[List[Dict]] = None, start_cursor: Optional[str] = None,
                    page_size: Optional[int] = None) -> Dict:
        """Query a database with optional filtering and sorting"""
        data = {}
        if filter_criteria:
            data["filter"] = filter_criteria
        if sorts:
            data["sorts"] = sorts
        if start_cursor:
            data["start_cursor"] = start_cursor
        if page_size:
            data["page_size"] = min(page_size, 100)
        
        return self._make_request("POST", f"databases/{database_id}/query", data)
    
    def create_database(self, parent: Dict, title: str, properties: Dict) -> Dict:
        """Create a new database"""
        data = {
            "parent": parent,
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties
        }
        return self._make_request("POST", "databases", data)
    
    def get_page(self, page_id: str) -> Dict:
        """Retrieve a page"""
        return self._make_request("GET", f"pages/{page_id}")
    
    def create_page(self, parent: Dict, properties: Dict, children: Optional[List[Dict]] = None) -> Dict:
        """Create a new page"""
        data = {
            "parent": parent,
            "properties": properties
        }
        if children:
            data["children"] = children
        
        return self._make_request("POST", "pages", data)
    
    def update_page(self, page_id: str, properties: Dict, archived: Optional[bool] = None) -> Dict:
        """Update page properties"""
        data = {"properties": properties}
        if archived is not None:
            data["archived"] = archived
        
        return self._make_request("PATCH", f"pages/{page_id}", data)
    
    def get_block_children(self, block_id: str, start_cursor: Optional[str] = None,
                          page_size: Optional[int] = None) -> Dict:
        """Get children of a block"""
        params = {}
        if start_cursor:
            params["start_cursor"] = start_cursor
        if page_size:
            params["page_size"] = min(page_size, 100)
        
        return self._make_request("GET", f"blocks/{block_id}/children", params=params)
    
    def append_block_children(self, block_id: str, children: List[Dict]) -> Dict:
        """Append children blocks to a parent block"""
        data = {"children": children}
        return self._make_request("PATCH", f"blocks/{block_id}/children", data)
    
    def search(self, query: Optional[str] = None, filter_criteria: Optional[Dict] = None,
              sorts: Optional[List[Dict]] = None, start_cursor: Optional[str] = None,
              page_size: Optional[int] = None) -> Dict:
        """Search across pages and databases"""
        data = {}
        if query:
            data["query"] = query
        if filter_criteria:
            data["filter"] = filter_criteria
        if sorts:
            data["sorts"] = sorts
        if start_cursor:
            data["start_cursor"] = start_cursor
        if page_size:
            data["page_size"] = min(page_size, 100)
        
        return self._make_request("POST", "search", data)
    
    def get_current_user(self) -> Dict:
        """Get the current bot user"""
        return self._make_request("GET", "users/me")

# Initialize the MCP server
server = Server("notion-mcp-server")

# Global client instance
notion_client: Optional[NotionClient] = None

def initialize_client():
    """Initialize the Notion client"""
    global notion_client
    try:
        notion_client = NotionClient(
            nango_connection_id=os.environ.get("NANGO_CONNECTION_ID"),
            nango_provider_config_key=os.environ.get("NANGO_INTEGRATION_ID")
        )
    except Exception as e:
        logging.error(f"Failed to initialize Notion client: {e}")
        raise

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Notion tools"""
    return [
        types.Tool(
            name="notion_search",
            description="Search across Notion pages and databases",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query text"},
                    "filter_type": {"type": "string", "enum": ["page", "database"], "description": "Filter by object type"},
                    "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Number of results to return"}
                }
            }
        ),
        types.Tool(
            name="notion_get_database",
            description="Get information about a Notion database",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_id": {"type": "string", "description": "The database ID"}
                },
                "required": ["database_id"]
            }
        ),
        types.Tool(
            name="notion_query_database",
            description="Query a Notion database with optional filtering and sorting",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_id": {"type": "string", "description": "The database ID"},
                    "filter_criteria": {"type": "object", "description": "Filter criteria for the query"},
                    "sorts": {"type": "array", "description": "Sort criteria"},
                    "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Number of results to return"}
                },
                "required": ["database_id"]
            }
        ),
        types.Tool(
            name="notion_create_database",
            description="Create a new Notion database",
            inputSchema={
                "type": "object",
                "properties": {
                    "parent_page_id": {"type": "string", "description": "Parent page ID where the database will be created"},
                    "title": {"type": "string", "description": "Database title"},
                    "properties": {"type": "object", "description": "Database schema properties"}
                },
                "required": ["parent_page_id", "title", "properties"]
            }
        ),
        types.Tool(
            name="notion_get_page",
            description="Get information about a Notion page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "The page ID"}
                },
                "required": ["page_id"]
            }
        ),
        types.Tool(
            name="notion_create_page",
            description="Create a new Notion page",
            inputSchema={
                "type": "object",
                "properties": {
                    "parent_type": {"type": "string", "enum": ["database", "page"], "description": "Type of parent"},
                    "parent_id": {"type": "string", "description": "Parent database or page ID"},
                    "properties": {"type": "object", "description": "Page properties"},
                    "children": {"type": "array", "description": "List of block children (optional)"}
                },
                "required": ["parent_type", "parent_id", "properties"]
            }
        ),
        types.Tool(
            name="notion_update_page",
            description="Update a Notion page's properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "The page ID"},
                    "properties": {"type": "object", "description": "Properties to update"},
                    "archived": {"type": "boolean", "description": "Whether to archive the page"}
                },
                "required": ["page_id", "properties"]
            }
        ),
        types.Tool(
            name="notion_get_block_children",
            description="Get children blocks of a Notion page or block",
            inputSchema={
                "type": "object",
                "properties": {
                    "block_id": {"type": "string", "description": "The block or page ID"},
                    "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Number of results to return"}
                },
                "required": ["block_id"]
            }
        ),
        types.Tool(
            name="notion_append_blocks",
            description="Append blocks to a Notion page",
            inputSchema={
                "type": "object",
                "properties": {
                    "block_id": {"type": "string", "description": "The parent block or page ID"},
                    "children": {"type": "array", "description": "List of blocks to append"}
                },
                "required": ["block_id", "children"]
            }
        ),
        types.Tool(
            name="notion_get_current_user",
            description="Get information about the current Notion integration user",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    if not notion_client:
        return [types.TextContent(type="text", text="Error: Notion client not initialized")]
    
    try:
        if name == "notion_search":
            query = arguments.get("query")
            filter_type = arguments.get("filter_type")
            page_size = arguments.get("page_size")
            
            filter_criteria = None
            if filter_type:
                filter_criteria = {"property": "object", "value": filter_type}
            
            result = notion_client.search(
                query=query,
                filter_criteria=filter_criteria,
                page_size=page_size
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "notion_get_database":
            database_id = arguments["database_id"]
            result = notion_client.get_database(database_id)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "notion_query_database":
            database_id = arguments["database_id"]
            filter_criteria = arguments.get("filter_criteria")
            sorts = arguments.get("sorts")
            page_size = arguments.get("page_size")
            
            result = notion_client.query_database(
                database_id=database_id,
                filter_criteria=filter_criteria,
                sorts=sorts,
                page_size=page_size
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "notion_create_database":
            parent_page_id = arguments["parent_page_id"]
            title = arguments["title"]
            properties = arguments["properties"]
            
            parent = {"type": "page_id", "page_id": parent_page_id}
            result = notion_client.create_database(parent, title, properties)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "notion_get_page":
            page_id = arguments["page_id"]
            result = notion_client.get_page(page_id)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "notion_create_page":
            parent_type = arguments["parent_type"]
            parent_id = arguments["parent_id"]
            properties = arguments["properties"]
            children = arguments.get("children")
            
            if parent_type == "database":
                parent = {"type": "database_id", "database_id": parent_id}
            else:
                parent = {"type": "page_id", "page_id": parent_id}
            
            result = notion_client.create_page(parent, properties, children)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "notion_update_page":
            page_id = arguments["page_id"]
            properties = arguments["properties"]
            archived = arguments.get("archived")
            
            result = notion_client.update_page(page_id, properties, archived)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "notion_get_block_children":
            block_id = arguments["block_id"]
            page_size = arguments.get("page_size")
            
            result = notion_client.get_block_children(block_id, page_size=page_size)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "notion_append_blocks":
            block_id = arguments["block_id"]
            children = arguments["children"]
            
            result = notion_client.append_block_children(block_id, children)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "notion_get_current_user":
            result = notion_client.get_current_user()
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        logging.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

async def main():
    """Main function to run the MCP server"""
    # Initialize the Notion client
    try:
        initialize_client()
    except Exception as e:
        logging.error(f"Failed to initialize: {e}")
        sys.exit(1)
    
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="notion-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

def run():
    """Run the main function in an asyncio event loop."""
    try:
        asyncio.run(main())
    except Exception as error:
        print(f"Fatal error in main(): {error}", file=sys.stderr)
        sys.exit(1)