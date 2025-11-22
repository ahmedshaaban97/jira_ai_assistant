import sqlite3
import json
from typing import Type, Dict, Any, List, Optional
from datetime import datetime
from contextlib import contextmanager

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# Global database connection (in-memory SQLite)
_db_connection: Optional[sqlite3.Connection] = None


def get_db_connection() -> sqlite3.Connection:
    """Get or create the in-memory SQLite database connection."""
    global _db_connection
    if _db_connection is None:
        _db_connection = sqlite3.connect(":memory:", check_same_thread=False)
        _db_connection.row_factory = sqlite3.Row  # Enable column access by name
        _initialize_database(_db_connection)
    return _db_connection


def _initialize_database(conn: sqlite3.Connection) -> None:
    """Initialize the database schema with all required tables."""
    cursor = conn.cursor()
    
    # Create AGENTS table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS AGENTS (
            agent_id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            agent_role TEXT NOT NULL,
            version TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create TOOL_CALLS table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TOOL_CALLS (
            tool_call_id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER,
            tool_name TEXT NOT NULL,
            status TEXT NOT NULL,
            input_payload_json TEXT,
            output_payload_json TEXT,
            duration_ms INTEGER,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agent_id) REFERENCES AGENTS(agent_id)
        )
    """)
    
    # Create EVENTS table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS EVENTS (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER,
            tool_call_id INTEGER,
            event_type TEXT NOT NULL,
            message TEXT,
            metadata_json TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agent_id) REFERENCES AGENTS(agent_id),
            FOREIGN KEY (tool_call_id) REFERENCES TOOL_CALLS(tool_call_id)
        )
    """)
    
    # Create JIRA_ACTIONS table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS JIRA_ACTIONS (
            jira_action_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_call_id INTEGER,
            action_type TEXT NOT NULL,
            jira_issue_key TEXT,
            epic_key TEXT,
            request_json TEXT,
            response_json TEXT,
            status TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tool_call_id) REFERENCES TOOL_CALLS(tool_call_id)
        )
    """)
    
    conn.commit()


@contextmanager
def get_db_cursor():
    """Context manager for database cursor operations."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a SQLite Row to a dictionary."""
    return dict(row)


def _rows_to_list(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    """Convert a list of SQLite Rows to a list of dictionaries."""
    return [_row_to_dict(row) for row in rows]


# Tool: UpdateDbTool
class UpdateDbToolInput(BaseModel):
    """Input schema for UpdateDbTool."""
    table_name: str = Field(..., description="The name of the table to update (e.g., 'AGENTS', 'TOOL_CALLS', 'EVENTS', 'JIRA_ACTIONS')")
    data: Dict[str, Any] = Field(..., description="Dictionary containing the data to insert or update. For updates, include the primary key field.")


class UpdateDbTool(BaseTool):
    name: str = "update_db"
    description: str = (
        "Updates or inserts data into the database tables (AGENTS, TOOL_CALLS, EVENTS, JIRA_ACTIONS). "
        "Returns True if successful, False otherwise. "
        "For inserts, provide all required fields. For updates, include the primary key field (e.g., agent_id, tool_call_id)."
    )
    args_schema: Type[BaseModel] = UpdateDbToolInput

    def _run(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        Updates or inserts data into the specified database table.
        
        Args:
            table_name: The name of the table (AGENTS, TOOL_CALLS, EVENTS, JIRA_ACTIONS)
            data: Dictionary containing the data to insert or update
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            table_name = table_name.upper()
            
            # Validate table name
            valid_tables = ['AGENTS', 'TOOL_CALLS', 'EVENTS', 'JIRA_ACTIONS']
            if table_name not in valid_tables:
                return False
            
            with get_db_cursor() as cursor:
                # Check if this is an update (has primary key) or insert
                primary_keys = {
                    'AGENTS': 'agent_id',
                    'TOOL_CALLS': 'tool_call_id',
                    'EVENTS': 'event_id',
                    'JIRA_ACTIONS': 'jira_action_id'
                }
                
                pk_field = primary_keys[table_name]
                is_update = pk_field in data and data[pk_field] is not None
                
                if is_update:
                    # Update existing record
                    pk_value = data[pk_field]
                    
                    # Make a copy to avoid modifying the original data
                    update_data = data.copy()
                    update_data.pop(pk_field)  # Remove PK from update data
                    
                    # Add updated_at timestamp only for tables that have this column
                    if table_name not in ['EVENTS', 'JIRA_ACTIONS']:
                        update_data['updated_at'] = datetime.now().isoformat()
                    
                    # Build UPDATE query
                    set_clauses = []
                    values = []
                    json_fields = ['input_payload_json', 'output_payload_json', 'metadata_json', 'request_json', 'response_json']
                    for key, value in update_data.items():
                        if key in json_fields:
                            # Serialize JSON fields (only if not already a string)
                            if value is not None and not isinstance(value, str):
                                value = json.dumps(value)
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                    
                    values.append(pk_value)
                    query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {pk_field} = ?"
                    cursor.execute(query, values)
                    
                else:
                    # Insert new record
                    # Handle JSON fields
                    processed_data = {}
                    json_fields = ['input_payload_json', 'output_payload_json', 'metadata_json', 'request_json', 'response_json']
                    for key, value in data.items():
                        if key in json_fields:
                            # Serialize JSON fields (only if not already a string)
                            if value is not None and not isinstance(value, str):
                                processed_data[key] = json.dumps(value)
                            else:
                                processed_data[key] = value if value is not None else None
                        else:
                            processed_data[key] = value
                    
                    # Add timestamps if not provided
                    if 'created_at' not in processed_data:
                        processed_data['created_at'] = datetime.now().isoformat()
                    # Only add updated_at for tables that have this column (AGENTS and TOOL_CALLS)
                    if 'updated_at' not in processed_data and table_name not in ['EVENTS', 'JIRA_ACTIONS']:
                        processed_data['updated_at'] = datetime.now().isoformat()
                    
                    # Build INSERT query
                    columns = list(processed_data.keys())
                    placeholders = ', '.join(['?'] * len(columns))
                    values = list(processed_data.values())
                    
                    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    cursor.execute(query, values)
                
                return True
                
        except Exception as e:
            print(f"Error in update_db: {str(e)}")
            return False


# Tool: GetDbTool
class GetDbToolInput(BaseModel):
    """Input schema for GetDbTool."""
    sql_query: str = Field(..., description="SQL SELECT query to execute on the database. Must be a SELECT query only.")


class GetDbTool(BaseTool):
    name: str = "get_db"
    description: str = (
        "Executes a SQL SELECT query on the database and returns the results as a table. "
        "Only SELECT queries are allowed. Returns results as a list of dictionaries where each dictionary represents a row."
    )
    args_schema: Type[BaseModel] = GetDbToolInput

    def _run(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Executes a SQL SELECT query and returns the results.
        
        Args:
            sql_query: SQL SELECT query to execute
        
        Returns:
            List[Dict[str, Any]]: List of dictionaries, each representing a row from the query results
        """
        try:
            # Basic security check - only allow SELECT queries
            sql_query_upper = sql_query.strip().upper()
            if not sql_query_upper.startswith('SELECT'):
                return []
            
            with get_db_cursor() as cursor:
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                return _rows_to_list(rows)
                
        except Exception as e:
            print(f"Error in get_db: {str(e)}")
            return []
