# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Model Context Protocol (MCP) server that provides database access to Microsoft SQL Server using the pymssql library. The server is designed as a single-file, dependency-inline executable using uv's script mode.

**Core Purpose:** Provide reliable MSSQL connectivity to MCP clients (like Claude Code) with both read and write operations.

## Architecture

### Single-File Design
- **server.py**: Complete MCP server implementation with inline dependencies
- Uses `#!/usr/bin/env -S uv run --script` shebang for direct execution
- Dependencies declared in PEP 723 inline script metadata: `pymssql>=2.2.0`, `mcp>=0.1.0`

### Key Components

1. **Database Connection** (server.py:30-38)
   - `get_connection()` creates pymssql connections using environment variables
   - Connections are opened per-operation and closed in finally blocks
   - No connection pooling - simple and reliable approach

2. **MCP Server Setup** (server.py:42)
   - Server instance named "climate-mssql-mcp"
   - Two decorators: `@app.list_tools()` and `@app.call_tool()`
   - Tools are dynamically registered based on READONLY environment variable

3. **Tool Categories**
   - **Read Operations** (always available): list_table, describe_table, read_data
   - **Write Operations** (when READONLY=false): insert_data, update_data, create_table, create_index, drop_table

4. **Environment Configuration** (server.py:22-27)
   ```
   SERVER_NAME    - MSSQL server hostname (with optional \INSTANCE)
   PORT           - Server port (default: 1433)
   DATABASE_NAME  - Target database
   SQL_USERNAME   - SQL authentication username
   SQL_PASSWORD   - SQL authentication password
   READONLY       - "true" disables write operations
   ```

## Development Commands

### Running the Server
```bash
# Make executable (first time only)
chmod +x server.py

# Run directly (uv handles dependencies automatically)
./server.py
```

### Testing Locally
The server uses stdio for MCP communication. To test:
1. Configure in `.mcp.json` with proper environment variables
2. Restart Claude Code to load the MCP server
3. Ask Claude to interact with the database

### Linting/Formatting
No specific linters configured. Follow PEP 8 conventions.

## Code Patterns

### Connection Management Pattern
All database operations follow this pattern:
```python
async def operation_name(...) -> str:
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # ... execute query
        conn.commit()  # for write operations
        return result
    except Exception as e:
        if conn:
            conn.rollback()  # for write operations
        raise
    finally:
        if conn:
            conn.close()
```

### Tool Handler Pattern
The `call_tool()` function dispatches to operation functions based on tool name and READONLY mode. All operations return `list[TextContent]` with either results or error messages.

### Query Safety
- **read_data**: Enforces queries must start with "SELECT"
- **Parameterized queries**: All user inputs use pymssql parameter substitution (`%s` placeholders)
- **No SQL injection protection for table/column names**: Assumes trusted MCP client usage

## Important Implementation Notes

1. **Named Instance Handling**: SQL Server named instances (e.g., `SQLEXPRESS`) are specified in SERVER_NAME with backslash: `hostname\SQLEXPRESS`

2. **Dictionary Cursors**: `read_data` uses `cursor(as_dict=True)` for JSON-friendly output

3. **Batch Inserts**: `insert_data` accepts either a single dict or array of dicts, iterating through all records

4. **Error Handling**: All errors are caught at `call_tool()` level and returned as text content, not exceptions

5. **No Async Database Calls**: pymssql is synchronous, wrapped in async functions for MCP compatibility

## Configuration for MCP Clients

The server expects to be configured in `.mcp.json`:
```json
{
  "mcpServers": {
    "MSSQL-MCP": {
      "command": "/absolute/path/to/server.py",
      "env": {
        "SERVER_NAME": "server\\INSTANCE",
        "DATABASE_NAME": "YourDB",
        "SQL_USERNAME": "user",
        "SQL_PASSWORD": "pass",
        "READONLY": "false"
      },
      "type": "stdio"
    }
  }
}
```

## Security Considerations

- Never commit `.mcp.json` with real credentials
- Use READONLY mode when write access isn't required
- Parameterized queries prevent SQL injection for values, but table/column names are directly interpolated
- Designed for trusted client usage (Claude Code), not public API exposure
