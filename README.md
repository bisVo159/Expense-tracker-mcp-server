# Expense Tracker MCP Server

A simple expense tracker server using FastMCP.

## Features

- Add, list, edit, delete, and summarize expenses
- Category management via `categories.json`

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv)
- fastmcp

## Setup

```sh
# 1. Clone the repository
git clone https://github.com/bisVo159/Expense-tracker-mcp-server.git

# 2. Go into the project folder
cd Expense-tracker-mcp-server

# 3. Install dependencies & create virtual environment
uv sync

# 4. Run the application
uv run fastmcp dev main.py
```

## Files

- `main.py`: Server code
- `categories.json`: Expense categories
- `expenses.db`: SQLite database

## Usage

Use an MCP client to call these tools:

- `add_expense`
- `list_expenses`
- `edit_expense`
- `delete_expense`
- `summarize`
- `get_categories`

## Claude Desktop Integration

To use this server with Claude Desktop, add the following to your `claude_desktop_config.json`:

```json
"Expense Tracker": {
  "command": "uv",
  "args": [
    "--directory",
    "path where you cloned this repository",
    "run",
    "main.py"
  ]
}
```