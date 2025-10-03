# Climate MSSQL MCP Server

A lightweight, reliable Model Context Protocol (MCP) server for Microsoft SQL Server using Python and pymssql.

## Why This MCP Server?

Built from frustration with connection issues in Node.js-based MSSQL MCP servers, this Python implementation uses the proven pymssql library for rock-solid SQL Server connectivity. No mysterious timeouts, no complex configuration - just working database access.

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Access to a Microsoft SQL Server instance
- [Claude Code](https://claude.com/claude-code) or any MCP-compatible client

## Quick Start

### 1. Clone or Download

```bash
git clone https://github.com/yourusername/climate_mssql_mcp.git
cd climate_mssql_mcp
```

### 2. Make the Server Executable

```bash
chmod +x server.py
```

That's it! The server uses `uv` with inline dependencies - no separate installation needed.

## Configuration for Claude Code

Add this to your project's `.mcp.json` file:

```json
{
  "mcpServers": {
    "MSSQL-MCP": {
      "command": "/absolute/path/to/climate_mssql_mcp/server.py",
      "env": {
        "SERVER_NAME": "your-server.domain.com\\SQLEXPRESS",
        "PORT": "1433",
        "DATABASE_NAME": "YourDatabase",
        "SQL_USERNAME": "your-username",
        "SQL_PASSWORD": "your-password",
        "READONLY": "false"
      },
      "type": "stdio"
    }
  }
}
```

### Configuration Options

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SERVER_NAME` | Yes | SQL Server hostname/IP with optional instance | `server.local\SQLEXPRESS` or `192.168.1.100` |
| `PORT` | No | SQL Server port (default: 1433) | `1433` |
| `DATABASE_NAME` | Yes | Database to connect to | `MyDatabase` |
| `SQL_USERNAME` | Yes | SQL Server username | `sa` |
| `SQL_PASSWORD` | Yes | SQL Server password | `MyP@ssw0rd` |
| `READONLY` | No | Set to "true" to disable write operations | `false` |

**Connection Behavior:**
- Connection timeout: 30 seconds (network operations)
- Login timeout: 15 seconds (authentication)
- Connections are opened per-operation and closed immediately after (no pooling)

### Connection String Format

For named instances (like SQLEXPRESS), use double backslashes in JSON:
```json
"SERVER_NAME": "hostname\\SQLEXPRESS"
```

For default instances or IP addresses:
```json
"SERVER_NAME": "hostname.domain.com"
```
or
```json
"SERVER_NAME": "192.168.1.100"
```

## Available Tools

### Read Operations (Always Available)

#### `list_table`
List all tables in the database or filter by schema.

**Parameters:**
- `parameters` (optional): Array of schema names to filter by

**Example:**
```
List all tables in dbo schema
```

#### `describe_table`
Show the schema/structure of a specific table.

**Parameters:**
- `tableName` (required): Name of the table

**Example:**
```
Describe the Media table
```

#### `read_data`
Execute SELECT queries against the database.

**Parameters:**
- `query` (required): SQL SELECT statement

**Example:**
```
Show me the top 10 artists from the Artists table
```

### Write Operations (When READONLY=false)

#### `insert_data`
Insert one or more records into a table.

**Parameters:**
- `tableName` (required): Target table name
- `data` (required): Single object or array of objects with column:value pairs

#### `update_data`
Update records in a table.

**Parameters:**
- `tableName` (required): Target table name
- `updates` (required): Object with column:value pairs to update
- `whereClause` (required): WHERE condition (without the "WHERE" keyword)

#### `create_table`
Create a new table.

**Parameters:**
- `tableName` (required): Name for new table
- `columns` (required): Array of column definitions with name, type, nullable, primaryKey

#### `create_index`
Create an index on a table.

**Parameters:**
- `tableName` (required): Table to index
- `indexName` (required): Name for the index
- `columns` (required): Array of column names
- `unique` (optional): true for unique index

#### `drop_table`
Delete a table from the database.

**Parameters:**
- `tableName` (required): Table to drop

## Usage in Claude Code

Once configured, simply ask Claude to interact with your database:

```
What tables are in the database?

Show me the schema of the Media table

Find all artists with names starting with 'The'

Create a test table called temp_data with id and name columns
```

Claude will automatically use the appropriate MCP tools to execute your requests.

## Troubleshooting

### Connection Fails
- Verify SQL Server is running and accessible
- Check firewall rules allow connections on the specified port
- Confirm SQL Server authentication is enabled (not just Windows auth)
- Test connection with a SQL client (Azure Data Studio, SSMS) using the same credentials

### Timeout Errors
- Connection attempts timeout after 15 seconds (login) or 30 seconds (operations)
- If you see timeout errors on a known-working server, check network latency
- For slow networks, you may need to adjust timeout values in server.py:39-40

### Permission Errors
- Ensure the SQL user has appropriate permissions on the target database
- For write operations, user needs INSERT/UPDATE/DELETE/CREATE/DROP permissions

### Module Import Errors
If you see import errors, ensure `uv` is installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Security Notes

- **Never commit `.mcp.json` with real credentials to version control**
- Use environment variables or secure credential storage for production
- Consider using read-only mode (`READONLY: "true"`) when write access isn't needed
- Restrict SQL user permissions to minimum required for your use case

## Technical Details

- **Language**: Python 3.10+
- **Database Driver**: pymssql 2.2.0+
- **MCP Protocol**: Model Context Protocol 0.1.0+
- **Dependency Management**: uv (inline script dependencies)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Issues and pull requests welcome! This project prioritizes simplicity and reliability over features.

## Acknowledgments

Built as a pragmatic alternative to Node.js MSSQL MCP implementations, proving that sometimes the best solution is the simplest one.
