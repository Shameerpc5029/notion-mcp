# 🚀 Notion MCP Server

A powerful Model Context Protocol (MCP) server that connects AI assistants like Claude to your Notion workspace. Seamlessly search, create, and manage your Notion content through natural language conversations!

## ✨ What This Does

Transform your AI assistant into a Notion powerhouse! With this MCP server, you can:

- 🔍 **Search** through all your Notion pages and databases
- 📝 **Create** new pages, databases, and content
- ✏️ **Update** existing pages and properties
- 📊 **Query** databases with complex filters
- 🔗 **Manage** your entire Notion workspace through conversation

## 🎯 Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- A Notion workspace
- Nango account (for OAuth authentication)
- Claude Desktop app (for AI integration)

### 2. Installation

```bash
# Clone or download the files
git clone <your-repo-url>
cd notion-mcp-server

# Install dependencies
uv sync
```

### 3. Notion Setup

1. **Create a Notion Integration:**
   - Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
   - Click "New integration"
   - Name it (e.g., "Claude MCP Integration")
   - Select your workspace
   - Set capabilities:
     - ✅ Read content
     - ✅ Insert content
     - ✅ Update content
   - Save and copy your integration token

2. **Share Pages with Integration:**
   - Open any Notion page you want to access
   - Click "Share" → "Invite" 
   - Select your integration
   - Repeat for all pages/databases you want to use

### 4. Nango Setup (OAuth)

1. **Create Nango Account:** [https://nango.dev](https://nango.dev)
2. **Add Notion Integration** in your Nango dashboard
3. **Configure OAuth** with your Notion integration credentials
4. **Get your Nango credentials** (Base URL, Secret Key, Connection ID)

### 5. Environment Configuration

Create a `.env` file with your credentials:

```env
# Nango OAuth Configuration
NANGO_BASE_URL=https://api.nango.dev
NANGO_SECRET_KEY=your_nango_secret_key_here
NANGO_CONNECTION_ID=your_connection_id_here
NANGO_INTEGRATION_ID=notion

# Optional: Direct Notion Token (if not using Nango)
# NOTION_TOKEN=your_direct_notion_token_here
```

### 6. Claude Desktop Configuration

Add this to your Claude Desktop configuration file:

**On macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**On Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "notion": {
      "command": "uvx",
      "args": ["git+https://github.com/Shameerpc5029/notion-mcp.git"],
      "env": {
        "NANGO_BASE_URL": "https://api.nango.dev",
        "NANGO_SECRET_KEY": "your_nango_secret_key",
        "NANGO_CONNECTION_ID": "your_connection_id", 
        "NANGO_INTEGRATION_ID": "notion"
      }
    }
  }
}
```

### 7. Test the Connection

```bash
# Test the server directly
python notion-mcp-server.py

# Or restart Claude Desktop and try asking:
# "Search my Notion for meeting notes"
# "Create a new task in my project database"
```

## 🛠️ Available Tools

| Tool | Description | Example Use |
|------|-------------|-------------|
| `notion_search` | Search across all content | "Find pages about project planning" |
| `notion_get_database` | Get database info | "Show me my tasks database structure" |
| `notion_query_database` | Query with filters | "Show incomplete tasks due this week" |
| `notion_create_database` | Create new databases | "Create a CRM database with contacts" |
| `notion_get_page` | Get page details | "Show me the content of my meeting notes" |
| `notion_create_page` | Create new pages | "Add a new task to my project database" |
| `notion_update_page` | Update existing pages | "Mark this task as completed" |
| `notion_get_block_children` | Get page content | "Read the content of this page" |
| `notion_append_blocks` | Add content to pages | "Add meeting notes to this page" |
| `notion_get_current_user` | Get integration info | "Check my Notion connection status" |

## 💬 Example Conversations with Claude

Once configured, you can have natural conversations like:

### Task Management
```
You: "Show me all my incomplete tasks"
Claude: [Queries your tasks database and shows open items]

You: "Create a new task called 'Review MCP integration' due next Friday"
Claude: [Creates the task with proper due date]

You: "Mark the first task as completed"
Claude: [Updates the task status to Done]
```

### Content Creation  
```
You: "Create a meeting notes page for today's standup"
Claude: [Creates a new page with meeting template]

You: "Add action items from our discussion to that page"
Claude: [Appends bullet points with the action items]
```

### Research & Organization
```
You: "Search for all pages mentioning 'API documentation'"
Claude: [Finds and lists relevant pages]

You: "Create a new database to track our API endpoints"
Claude: [Creates a structured database with relevant properties]
```

## 🔧 Troubleshooting

### Common Issues

**"Authentication Error"**
- Check your `.env` file has correct Nango credentials
- Verify your Nango integration is active
- Ensure your Notion integration has proper capabilities

**"Page not found" errors**
- Make sure you've shared the page/database with your integration
- Check the page/database ID is correct
- Verify the integration has read access

**Claude can't find the server**
- Check the absolute path in `claude_desktop_config.json` is correct
- Ensure Python is in your system PATH
- Try running the server manually first to test

**"No access token found"**
- Verify Nango connection is working
- Check your `NANGO_CONNECTION_ID` matches your actual connection
- Try refreshing your Nango integration

### Debug Mode

Run with verbose logging:
```bash
python notion-mcp-server.py --debug
```

### Manual Testing

Test individual functions:
```python
from notion_mcp_server import NotionClient

client = NotionClient()
user = client.get_current_user()
print(f"Connected as: {user.get('name')}")
```

## 🔒 Security Notes

- **Never commit your `.env` file** to version control
- Keep your Nango secret key secure
- Only share Notion pages that the integration needs access to
- Regularly review your integration's access in Notion settings

## 📁 File Structure

```
notion-mcp/
├── main.py    # Main MCP server
├── pyproject.toml        # Python dependencies  
├── .env.example
├── .env                   # Your credentials (don't commit!)
├── README.md              # This file
```

## 🆘 Getting Help

1. **Check the logs** - Look for error messages in Claude Desktop or terminal
2. **Verify permissions** - Ensure your integration can access the pages
3. **Test manually** - Run the server directly to isolate issues
4. **Check Notion status** - Sometimes Notion API has outages

## 🎉 What's Next?

Once you're up and running:

- Try creating complex database queries
- Set up automated content creation workflows  
- Use Claude to help organize and restructure your Notion workspace
- Explore advanced filtering and sorting options

## 📄 License

This project is open source. Feel free to modify and adapt for your needs!

---

**Happy Notion-ing with Claude! 🎊**

*Made with ❤️ for the AI-powered productivity enthusiasts*