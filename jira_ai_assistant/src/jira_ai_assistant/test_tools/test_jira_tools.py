"""
Test script for Jira tools.
This script tests all three Jira tools: JiraAddCommentTool, JiraAssignIssueTool, and JiraGetUserHistoryTool.

Usage:
    # Run from the project root (jira_ai_assistant/ directory):
    uv run python src/jira_ai_assistant/test_tools/test_jira_tools.py
    
    # Or run directly:
    uv run python -m jira_ai_assistant.test_tools.test_jira_tools

Make sure you have:
1. Created a .env file with JIRA_URL, EMAIL, and API_KEY in jira_ai_assistant/.env
2. Have valid Jira credentials
3. Have test issue keys and account IDs to use (update them in this script)
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import the tools
# This script is at: jira_ai_assistant/src/jira_ai_assistant/test_tools/test_jira_tools.py
# We need to add: jira_ai_assistant/src to the path
script_dir = Path(__file__).resolve().parent  # test_tools/
src_dir = script_dir.parent.parent  # src/
sys.path.insert(0, str(src_dir))

from jira_ai_assistant.tools.jira_tools import (
    JiraAddCommentTool,
    JiraAssignIssueTool,
    JiraGetUserHistoryTool,
    JiraCreateIssueTool,
)


def test_jira_add_comment():
    """Test adding a comment to a Jira issue."""
    print("\n" + "="*60)
    print("Testing JiraAddCommentTool")
    print("="*60)
    
    tool = JiraAddCommentTool()
    
    # TODO: Replace with your test issue key
    issue_key = "MH-9"  # Change this to a valid issue key in your Jira instance
    comment_body = "This is a test comment from the AI assistant tool."
    
    print(f"\nAdding comment to issue: {issue_key}")
    print(f"Comment: {comment_body}")
    
    try:
        result = tool._run(issue_key=issue_key, body=comment_body)
        print("\n✓ Comment added successfully!")
        print(f"Comment ID: {result.get('id')}")
        print(f"Comment created: {result.get('created')}")
        return True
    except Exception as e:
        print(f"\n✗ Error adding comment: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def test_jira_assign_issue():
    """Test assigning a Jira issue to a user."""
    print("\n" + "="*60)
    print("Testing JiraAssignIssueTool")
    print("="*60)
    
    tool = JiraAssignIssueTool()
    
    # TODO: Replace with your test issue key and account ID
    issue_key = "MH-9"  # Change this to a valid issue key
    assignee_account_id = "5fcfd938e40b82006e36206f"  # Change this to a valid account ID
    
    print(f"\nAssigning issue {issue_key} to account ID: {assignee_account_id}")
    
    try:
        result = tool._run(issue_key=issue_key, assignee_account_id=assignee_account_id)
        print("\n✓ Issue assigned successfully!")
        if result:
            print(f"Response: {result}")
        return True
    except Exception as e:
        print(f"\n✗ Error assigning issue: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def test_jira_get_user_history():
    """Test getting user history from Jira."""
    print("\n" + "="*60)
    print("Testing JiraGetUserHistoryTool")
    print("="*60)
    
    tool = JiraGetUserHistoryTool()
    
    # TODO: Replace with your test account ID
    account_id = "5fcfd938e40b82006e36206f"  # Change this to a valid account ID
    
    print(f"\nGetting history for account ID: {account_id}")
    
    try:
        user_history = tool._run(account_id=account_id)
        print(f"\n✓ Found {len(user_history)} issues assigned to user")
        
        # Display first 5 issues as a sample
        print("\nSample issues (first 5):")
        for i, (issue_key, issue_info) in enumerate(list(user_history.items())[:5]):
            print(f"\n  {issue_key}:")
            print(f"    Type: {issue_info.get('issue_type')}")
            print(f"    Status: {issue_info.get('status')}")
            print(f"    Summary: {issue_info.get('summary')}")
            print(f"    Start Date: {issue_info.get('start_date')}")
            print(f"    Due Date: {issue_info.get('due_date')}")
            if issue_info.get('work_log'):
                print(f"    Work Log: {issue_info.get('work_log')[:100]}...")
        
        if len(user_history) > 5:
            print(f"\n  ... and {len(user_history) - 5} more issues")
        
        return True
    except Exception as e:
        print(f"\n✗ Error getting user history: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def check_environment():
    """Check if environment variables are set."""
    import os
    print("\n" + "="*60)
    print("Checking Environment Configuration")
    print("="*60)
    
    jira_url = os.getenv("JIRA_URL", "")
    email = os.getenv("EMAIL", "")
    api_key = os.getenv("API_KEY", "")
    
    print(f"\nJIRA_URL: {'✓ Set' if jira_url else '✗ Not set'}")
    print(f"EMAIL: {'✓ Set' if email else '✗ Not set'}")
    print(f"API_KEY: {'✓ Set' if api_key else '✗ Not set'}")
    
    if not all([jira_url, email, api_key]):
        print("\n⚠ Warning: Some environment variables are not set!")
        print("Please create a .env file in jira_ai_assistant/ directory with:")
        print("  JIRA_URL=your_jira_url")
        print("  EMAIL=your_email")
        print("  API_KEY=your_api_key")
        return False
    
    return True


def test_jira_create_issue():
    """Test creating a Jira issue."""
    print("\n" + "="*60)
    print("Testing JiraCreateIssueTool")
    print("="*60)
    
    tool = JiraCreateIssueTool()
    
    # TODO: Replace with your test issue key and account ID
    project_key = 'MH'
    summary = 'Test Story 4'
    description = 'This is a test story'
    issue_type = 'Task'
    epic_key = 'MH-7'
    parent_key = None
    start_date = '2025-12-01'
    due_date = '2025-12-05'
    # assignee = '5fcfd938e40b82006e36206f'
    assignee = None
    story_points = 1

    print(f"\nCreating issue: {summary}")
    print(f"Project Key: {project_key}")
    print(f"Epic Key: {epic_key}")
    print(f"Parent Key: {parent_key}")
    print(f"Start Date: {start_date}")
    print(f"Due Date: {due_date}")
    print(f"Assignee: {assignee}")
    print(f"Story Points: {story_points}")

    try:
        result = tool._run(project_key=project_key, summary=summary, description=description, issue_type=issue_type, epic_key=epic_key, parent_key=parent_key, start_date=start_date, due_date=due_date, assignee=assignee, story_points=story_points)
        print("\n✓ Issue created successfully!")
        print(f"Issue Key: {result.get('issue_key')}")
        print(f"Issue ID: {result.get('issue_id')}")
        return True
    except Exception as e:
        print(f"\n✗ Error creating issue: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Jira Tools Test Suite")
    print("="*60)
    
    # Check environment first
    if not check_environment():
        print("\n⚠ Please configure your environment variables before running tests.")
        return
    
    results = []
    
    # Test each tool
    print("\n\nStarting tool tests...")
    print("\nNote: Make sure to update the test values (issue keys, account IDs) in this script!")
    
    # Test 1: Add Comment
    # results.append(("Add Comment", test_jira_add_comment()))
    
    # Test 2: Assign Issue
    # results.append(("Assign Issue", test_jira_assign_issue()))
    
    # Test 3: Get User History
    # results.append(("Get User History", test_jira_get_user_history()))

    # Test 4: Create Issue
    results.append(("Create Issue", test_jira_create_issue()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")


if __name__ == "__main__":
    main()

