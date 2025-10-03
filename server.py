#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pymssql>=2.2.0", "mcp>=0.1.0"]
# ///
"""
Climate MSSQL MCP Server
A Model Context Protocol server for MSSQL using pymssql
"""

import asyncio
import os
import sys
from typing import Any, Optional

import pymssql
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Database configuration from environment
DB_SERVER = os.getenv("SERVER_NAME", "localhost")
DB_PORT = int(os.getenv("PORT", "1433"))
DB_NAME = os.getenv("DATABASE_NAME", "master")
DB_USER = os.getenv("SQL_USERNAME", "")
DB_PASSWORD = os.getenv("SQL_PASSWORD", "")
READONLY = os.getenv("READONLY", "false").lower() == "true"


def get_connection() -> pymssql.Connection:
    """Create and return a database connection"""
    return pymssql.connect(
        server=DB_SERVER,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )


# Create MCP server
app = Server("climate-mssql-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    tools = [
        Tool(
            name="list_table",
            description="Lists tables in the MSSQL Database, or list tables in specific schemas",
            inputSchema={
                "type": "object",
                "properties": {
                    "parameters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Schemas to filter by (optional)",
                        "minItems": 0
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="describe_table",
            description="Describes the schema (columns and types) of a specified MSSQL Database table",
            inputSchema={
                "type": "object",
                "properties": {
                    "tableName": {
                        "type": "string",
                        "description": "Name of the table to describe"
                    }
                },
                "required": ["tableName"]
            }
        ),
        Tool(
            name="read_data",
            description="Executes a SELECT query on an MSSQL Database table",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute (must start with SELECT)"
                    }
                },
                "required": ["query"]
            }
        ),
    ]

    # Add write tools if not readonly
    if not READONLY:
        tools.extend([
            Tool(
                name="insert_data",
                description="Inserts data into an MSSQL Database table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tableName": {
                            "type": "string",
                            "description": "Name of the table to insert into"
                        },
                        "data": {
                            "oneOf": [
                                {
                                    "type": "object",
                                    "description": "Single record data object"
                                },
                                {
                                    "type": "array",
                                    "items": {"type": "object"},
                                    "description": "Array of data objects for multiple records"
                                }
                            ]
                        }
                    },
                    "required": ["tableName", "data"]
                }
            ),
            Tool(
                name="update_data",
                description="Updates data in an MSSQL Database table using a WHERE clause",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tableName": {
                            "type": "string",
                            "description": "Name of the table to update"
                        },
                        "updates": {
                            "type": "object",
                            "description": "Key-value pairs of columns to update"
                        },
                        "whereClause": {
                            "type": "string",
                            "description": "WHERE clause to identify which records to update"
                        }
                    },
                    "required": ["tableName", "updates", "whereClause"]
                }
            ),
            Tool(
                name="create_table",
                description="Creates a new table in the database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tableName": {
                            "type": "string",
                            "description": "Name of the table to create"
                        },
                        "columns": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "nullable": {"type": "boolean"},
                                    "primaryKey": {"type": "boolean"}
                                },
                                "required": ["name", "type"]
                            },
                            "description": "Column definitions"
                        }
                    },
                    "required": ["tableName", "columns"]
                }
            ),
            Tool(
                name="create_index",
                description="Creates an index on a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tableName": {
                            "type": "string",
                            "description": "Name of the table"
                        },
                        "indexName": {
                            "type": "string",
                            "description": "Name of the index"
                        },
                        "columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Columns to index"
                        },
                        "unique": {
                            "type": "boolean",
                            "description": "Whether the index should be unique"
                        }
                    },
                    "required": ["tableName", "indexName", "columns"]
                }
            ),
            Tool(
                name="drop_table",
                description="Drops a table from the database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tableName": {
                            "type": "string",
                            "description": "Name of the table to drop"
                        }
                    },
                    "required": ["tableName"]
                }
            ),
        ])

    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name == "list_table":
            result = await list_tables(arguments.get("parameters", []))
        elif name == "describe_table":
            result = await describe_table(arguments["tableName"])
        elif name == "read_data":
            result = await read_data(arguments["query"])
        elif name == "insert_data" and not READONLY:
            result = await insert_data(arguments["tableName"], arguments["data"])
        elif name == "update_data" and not READONLY:
            result = await update_data(
                arguments["tableName"],
                arguments["updates"],
                arguments["whereClause"]
            )
        elif name == "create_table" and not READONLY:
            result = await create_table(arguments["tableName"], arguments["columns"])
        elif name == "create_index" and not READONLY:
            result = await create_index(
                arguments["tableName"],
                arguments["indexName"],
                arguments["columns"],
                arguments.get("unique", False)
            )
        elif name == "drop_table" and not READONLY:
            result = await drop_table(arguments["tableName"])
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error occurred: {e}")]


async def list_tables(schemas: list[str] = None) -> str:
    """List all tables in the database"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if schemas and len(schemas) > 0:
            placeholders = ','.join(['%s'] * len(schemas))
            query = f"""
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_SCHEMA IN ({placeholders})
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            cursor.execute(query, schemas)
        else:
            query = """
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            cursor.execute(query)

        tables = cursor.fetchall()
        result = "\n".join([f"{schema}.{table}" for schema, table in tables])
        return result if result else "No tables found"
    finally:
        if conn:
            conn.close()


async def describe_table(table_name: str) -> str:
    """Describe the schema of a table"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        cursor.execute(query, (table_name,))
        columns = cursor.fetchall()

        if not columns:
            return f"Table '{table_name}' not found"

        result = []
        for col_name, data_type, max_len, nullable, default in columns:
            col_info = f"{col_name} {data_type}"
            if max_len:
                col_info += f"({max_len})"
            if nullable == "NO":
                col_info += " NOT NULL"
            if default:
                col_info += f" DEFAULT {default}"
            result.append(col_info)

        return "\n".join(result)
    finally:
        if conn:
            conn.close()


async def read_data(query: str) -> str:
    """Execute a SELECT query"""
    if not query.strip().upper().startswith("SELECT"):
        raise ValueError("Query must start with SELECT")

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            return "No results found"

        # Format as JSON-like output
        import json
        return json.dumps(rows, indent=2, default=str)
    finally:
        if conn:
            conn.close()


async def insert_data(table_name: str, data: Any) -> str:
    """Insert data into a table"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Handle single or multiple records
        records = [data] if isinstance(data, dict) else data

        if not records:
            return "No data to insert"

        # Get column names from first record
        columns = list(records[0].keys())
        placeholders = ','.join(['%s'] * len(columns))
        col_names = ','.join(columns)

        query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"

        # Insert all records
        for record in records:
            values = [record[col] for col in columns]
            cursor.execute(query, values)

        conn.commit()
        return f"Inserted {len(records)} record(s)"
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


async def update_data(table_name: str, updates: dict, where_clause: str) -> str:
    """Update data in a table"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        set_clause = ', '.join([f"{col} = %s" for col in updates.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

        cursor.execute(query, list(updates.values()))
        conn.commit()

        return f"Updated {cursor.rowcount} record(s)"
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


async def create_table(table_name: str, columns: list[dict]) -> str:
    """Create a new table"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Build column definitions
        col_defs = []
        pk_cols = []
        for col in columns:
            col_def = f"{col['name']} {col['type']}"
            if not col.get('nullable', True):
                col_def += " NOT NULL"
            col_defs.append(col_def)
            if col.get('primaryKey', False):
                pk_cols.append(col['name'])

        # Add primary key constraint if specified
        if pk_cols:
            col_defs.append(f"PRIMARY KEY ({', '.join(pk_cols)})")

        query = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
        cursor.execute(query)
        conn.commit()

        return f"Table '{table_name}' created successfully"
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


async def create_index(table_name: str, index_name: str, columns: list[str], unique: bool = False) -> str:
    """Create an index on a table"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        unique_keyword = "UNIQUE " if unique else ""
        cols = ', '.join(columns)
        query = f"CREATE {unique_keyword}INDEX {index_name} ON {table_name} ({cols})"

        cursor.execute(query)
        conn.commit()

        return f"Index '{index_name}' created successfully"
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


async def drop_table(table_name: str) -> str:
    """Drop a table"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = f"DROP TABLE {table_name}"
        cursor.execute(query)
        conn.commit()

        return f"Table '{table_name}' dropped successfully"
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
