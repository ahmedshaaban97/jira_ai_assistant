"""
Test script for Database tools.
This script tests both database tools: UpdateDbTool and GetDbTool.

Usage:
    # Run from the project root (jira_ai_assistant/ directory):
    uv run python src/jira_ai_assistant/test_tools/test_db_tools.py
    
    # Or run directly:
    uv run python -m jira_ai_assistant.test_tools.test_db_tools

This script tests:
1. Insert operations into all tables (AGENTS, TOOL_CALLS, EVENTS, JIRA_ACTIONS)
2. Update operations on existing records
3. SELECT queries to retrieve data
4. Foreign key relationships
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import the tools
# This script is at: jira_ai_assistant/src/jira_ai_assistant/test_tools/test_db_tools.py
# We need to add: jira_ai_assistant/src to the path
script_dir = Path(__file__).resolve().parent  # test_tools/
src_dir = script_dir.parent.parent  # src/
sys.path.insert(0, str(src_dir))

from jira_ai_assistant.tools.db_tools import (
    UpdateDbTool,
    GetDbTool,
    get_db_connection,
)


def test_insert_agent():
    """Test inserting an agent into the AGENTS table."""
    print("\n" + "="*60)
    print("Testing Insert into AGENTS table")
    print("="*60)
    
    tool = UpdateDbTool()
    
    agent_data = {
        "agent_name": "main_executor",
        "agent_role": "executor",
        "version": "1.0.0"
    }
    
    print(f"\nInserting agent: {agent_data}")
    
    try:
        result = tool._run(table_name="AGENTS", data=agent_data)
        if result:
            print("✓ Agent inserted successfully!")
            
            # Retrieve the inserted agent
            get_tool = GetDbTool()
            query_result = get_tool._run("SELECT * FROM AGENTS WHERE agent_name = 'main_executor'")
            if query_result:
                print(f"Retrieved agent: {query_result[0]}")
                return query_result[0].get('agent_id')
            return True
        else:
            print("✗ Failed to insert agent")
            return None
    except Exception as e:
        print(f"✗ Error inserting agent: {e}")
        return None


def test_insert_tool_call(agent_id):
    """Test inserting a tool call into the TOOL_CALLS table."""
    print("\n" + "="*60)
    print("Testing Insert into TOOL_CALLS table")
    print("="*60)
    
    tool = UpdateDbTool()
    
    tool_call_data = {
        "agent_id": agent_id,
        "tool_name": "jira_create_issue",
        "status": "success",
        "input_payload_json": {"issue_key": "TEST-123", "summary": "Test issue"},
        "output_payload_json": {"id": "12345", "key": "TEST-123"},
        "duration_ms": 250
    }
    
    print(f"\nInserting tool call: {tool_call_data}")
    
    try:
        result = tool._run(table_name="TOOL_CALLS", data=tool_call_data)
        if result:
            print("✓ Tool call inserted successfully!")
            
            # Retrieve the inserted tool call
            get_tool = GetDbTool()
            query_result = get_tool._run(f"SELECT * FROM TOOL_CALLS WHERE agent_id = {agent_id}")
            if query_result:
                print(f"Retrieved tool call: {query_result[0]}")
                return query_result[0].get('tool_call_id')
            return True
        else:
            print("✗ Failed to insert tool call")
            return None
    except Exception as e:
        print(f"✗ Error inserting tool call: {e}")
        return None


def test_insert_event(agent_id, tool_call_id):
    """Test inserting an event into the EVENTS table."""
    print("\n" + "="*60)
    print("Testing Insert into EVENTS table")
    print("="*60)
    
    tool = UpdateDbTool()
    
    event_data = {
        "agent_id": agent_id,
        "tool_call_id": tool_call_id,
        "event_type": "TOOL_CALL",
        "message": "Successfully created Jira issue",
        "metadata_json": {"priority": "high", "assignee": "user123"}
    }
    
    print(f"\nInserting event: {event_data}")
    
    try:
        result = tool._run(table_name="EVENTS", data=event_data)
        if result:
            print("✓ Event inserted successfully!")
            
            # Retrieve the inserted event
            get_tool = GetDbTool()
            query_result = get_tool._run(f"SELECT * FROM EVENTS WHERE agent_id = {agent_id}")
            if query_result:
                print(f"Retrieved event: {query_result[0]}")
                return query_result[0].get('event_id')
            return True
        else:
            print("✗ Failed to insert event")
            return None
    except Exception as e:
        print(f"✗ Error inserting event: {e}")
        return None


def test_insert_jira_action(tool_call_id):
    """Test inserting a Jira action into the JIRA_ACTIONS table."""
    print("\n" + "="*60)
    print("Testing Insert into JIRA_ACTIONS table")
    print("="*60)
    
    tool = UpdateDbTool()
    
    jira_action_data = {
        "tool_call_id": tool_call_id,
        "action_type": "create_issue",
        "jira_issue_key": "TEST-123",
        "epic_key": "EPIC-1",
        "request_json": {"summary": "Test issue", "description": "This is a test"},
        "response_json": {"id": "12345", "key": "TEST-123", "self": "https://jira.example.com/rest/api/3/issue/12345"},
        "status": "success"
    }
    
    print(f"\nInserting Jira action: {jira_action_data}")
    
    try:
        result = tool._run(table_name="JIRA_ACTIONS", data=jira_action_data)
        if result:
            print("✓ Jira action inserted successfully!")
            
            # Retrieve the inserted Jira action
            get_tool = GetDbTool()
            query_result = get_tool._run(f"SELECT * FROM JIRA_ACTIONS WHERE tool_call_id = {tool_call_id}")
            if query_result:
                print(f"Retrieved Jira action: {query_result[0]}")
                return query_result[0].get('jira_action_id')
            return True
        else:
            print("✗ Failed to insert Jira action")
            return None
    except Exception as e:
        print(f"✗ Error inserting Jira action: {e}")
        return None


def test_update_agent(agent_id):
    """Test updating an agent in the AGENTS table."""
    print("\n" + "="*60)
    print("Testing Update in AGENTS table")
    print("="*60)
    
    tool = UpdateDbTool()
    
    update_data = {
        "agent_id": agent_id,
        "version": "1.1.0",
        "agent_role": "executor"
    }
    
    print(f"\nUpdating agent {agent_id}: {update_data}")
    
    try:
        result = tool._run(table_name="AGENTS", data=update_data)
        if result:
            print("✓ Agent updated successfully!")
            
            # Retrieve the updated agent
            get_tool = GetDbTool()
            query_result = get_tool._run(f"SELECT * FROM AGENTS WHERE agent_id = {agent_id}")
            if query_result:
                print(f"Updated agent: {query_result[0]}")
                if query_result[0].get('version') == "1.1.0":
                    print("✓ Version correctly updated!")
                    return True
            return False
        else:
            print("✗ Failed to update agent")
            return False
    except Exception as e:
        print(f"✗ Error updating agent: {e}")
        return False


def test_get_db_queries():
    """Test various SELECT queries."""
    print("\n" + "="*60)
    print("Testing GetDbTool with various SELECT queries")
    print("="*60)
    
    tool = GetDbTool()
    
    queries = [
        ("SELECT * FROM AGENTS", "Get all agents"),
        ("SELECT * FROM TOOL_CALLS", "Get all tool calls"),
        ("SELECT * FROM EVENTS", "Get all events"),
        ("SELECT * FROM JIRA_ACTIONS", "Get all Jira actions"),
        ("SELECT a.agent_name, COUNT(t.tool_call_id) as tool_count FROM AGENTS a LEFT JOIN TOOL_CALLS t ON a.agent_id = t.agent_id GROUP BY a.agent_id", "Get agent tool call counts"),
        ("SELECT e.event_type, COUNT(*) as count FROM EVENTS e GROUP BY e.event_type", "Get event type counts"),
    ]
    
    results = []
    for query, description in queries:
        print(f"\nQuery: {description}")
        print(f"SQL: {query}")
        try:
            result = tool._run(sql_query=query)
            print(f"✓ Query executed successfully! Returned {len(result)} rows")
            if result:
                print(f"Sample row: {result[0]}")
            results.append(True)
        except Exception as e:
            print(f"✗ Error executing query: {e}")
            results.append(False)
    
    return all(results)


def test_get_db_security():
    """Test that get_db only allows SELECT queries."""
    print("\n" + "="*60)
    print("Testing GetDbTool Security (should reject non-SELECT queries)")
    print("="*60)
    
    tool = GetDbTool()
    
    malicious_queries = [
        ("DELETE FROM AGENTS", "DELETE query"),
        ("UPDATE AGENTS SET agent_name = 'hacked'", "UPDATE query"),
        ("DROP TABLE AGENTS", "DROP query"),
        ("INSERT INTO AGENTS (agent_name) VALUES ('hacked')", "INSERT query"),
    ]
    
    all_blocked = True
    for query, description in malicious_queries:
        print(f"\nTesting {description}: {query}")
        try:
            result = tool._run(sql_query=query)
            if result == []:
                print("✓ Query correctly blocked (returned empty result)")
            else:
                print(f"✗ Query was not blocked! Returned: {result}")
                all_blocked = False
        except Exception as e:
            print(f"✓ Query correctly blocked (exception: {type(e).__name__})")
    
    return all_blocked


def test_foreign_key_relationships():
    """Test foreign key relationships between tables."""
    print("\n" + "="*60)
    print("Testing Foreign Key Relationships")
    print("="*60)
    
    tool = GetDbTool()
    
    try:
        # Test JOIN query to verify relationships
        query = """
        SELECT 
            a.agent_name,
            a.agent_role,
            t.tool_name,
            t.status,
            e.event_type,
            e.message,
            j.action_type,
            j.jira_issue_key
        FROM AGENTS a
        LEFT JOIN TOOL_CALLS t ON a.agent_id = t.agent_id
        LEFT JOIN EVENTS e ON t.tool_call_id = e.tool_call_id
        LEFT JOIN JIRA_ACTIONS j ON t.tool_call_id = j.tool_call_id
        ORDER BY a.agent_id, t.tool_call_id
        """
        
        result = tool._run(sql_query=query)
        print(f"✓ JOIN query executed successfully! Returned {len(result)} rows")
        if result:
            print("\nSample joined data:")
            for i, row in enumerate(result[:3]):  # Show first 3 rows
                print(f"\n  Row {i+1}:")
                for key, value in row.items():
                    print(f"    {key}: {value}")
        return True
    except Exception as e:
        print(f"✗ Error testing foreign key relationships: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Database Tools Test Suite")
    print("="*60)
    
    results = []
    
    # Initialize database connection
    print("\nInitializing database...")
    try:
        conn = get_db_connection()
        print("✓ Database initialized successfully!")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        return
    
    # Test 1: Insert Agent
    print("\n\nStarting insert tests...")
    agent_id = test_insert_agent()
    if agent_id:
        results.append(("Insert Agent", True))
    else:
        results.append(("Insert Agent", False))
        print("\n⚠ Cannot continue tests without agent_id. Stopping.")
        return
    
    # Test 2: Insert Tool Call
    tool_call_id = test_insert_tool_call(agent_id)
    if tool_call_id:
        results.append(("Insert Tool Call", True))
    else:
        results.append(("Insert Tool Call", False))
        tool_call_id = None  # Continue with other tests
    
    # Test 3: Insert Event
    event_id = test_insert_event(agent_id, tool_call_id)
    if event_id:
        results.append(("Insert Event", True))
    else:
        results.append(("Insert Event", False))
    
    # Test 4: Insert Jira Action
    if tool_call_id:
        jira_action_id = test_insert_jira_action(tool_call_id)
        if jira_action_id:
            results.append(("Insert Jira Action", True))
        else:
            results.append(("Insert Jira Action", False))
    else:
        print("\n⚠ Skipping Jira Action insert test (no tool_call_id)")
        results.append(("Insert Jira Action", False))
    
    # Test 5: Update Agent
    print("\n\nStarting update tests...")
    update_result = test_update_agent(agent_id)
    results.append(("Update Agent", update_result))
    
    # Test 6: Get DB Queries
    print("\n\nStarting SELECT query tests...")
    get_result = test_get_db_queries()
    results.append(("Get DB Queries", get_result))
    
    # Test 7: Security Test
    security_result = test_get_db_security()
    results.append(("Security Test", security_result))
    
    # Test 8: Foreign Key Relationships
    fk_result = test_foreign_key_relationships()
    results.append(("Foreign Key Relationships", fk_result))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠ {len(results) - total_passed} test(s) failed")


if __name__ == "__main__":
    main()

