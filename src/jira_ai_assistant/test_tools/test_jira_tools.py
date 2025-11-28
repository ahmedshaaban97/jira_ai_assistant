"""
Test script for Jira tools.
This script tests four Jira tools: JiraAddCommentTool, JiraAssignIssueTool, JiraGetUserHistoryTool, and JiraGetAllUsersTool.

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
    JiraGetAllUsersTool,
    JiraGetUserHistoryTool,
    JiraGetIssueDetailsTool,
    JiraCreateIssueTool,
    JiraCreateSprintTool,
    JiraGetAllSprintsTool,
    JiraGetSprintIssuesTool,
    JiraMoveIssueToSprintTool,
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


def test_jira_get_issue_details():
    """Test getting detailed information about a specific Jira issue."""
    print("\n" + "="*60)
    print("Testing JiraGetIssueDetailsTool")
    print("="*60)
    
    tool = JiraGetIssueDetailsTool()
    
    # TODO: Replace with your test issue key
    issue_key = "MH-205"  # Change this to a valid issue key in your Jira instance
    
    print(f"\nGetting details for issue: {issue_key}")
    
    try:
        issue_details = tool._run(issue_key=issue_key)
        print(f"\n✓ Successfully retrieved issue details!")
        
        # Display key information
        print(f"\nIssue Key: {issue_details.get('issue_key')}")
        print(f"Issue ID: {issue_details.get('issue_id')}")
        print(f"Summary: {issue_details.get('summary')}")
        print(f"Issue Type: {issue_details.get('issue_type')}")
        print(f"Status: {issue_details.get('status')}")
        print(f"Priority: {issue_details.get('priority')}")
        print(f"Created: {issue_details.get('created')}")
        print(f"Updated: {issue_details.get('updated')}")
        
        # Assignee info
        assignee = issue_details.get('assignee')
        if assignee:
            print(f"\nAssignee:")
            print(f"  Display Name: {assignee.get('display_name')}")
            print(f"  Account ID: {assignee.get('account_id')}")
            print(f"  Email: {assignee.get('email')}")
        else:
            print(f"\nAssignee: Unassigned")
        
        # Reporter info
        reporter = issue_details.get('reporter')
        if reporter:
            print(f"\nReporter:")
            print(f"  Display Name: {reporter.get('display_name')}")
            print(f"  Account ID: {reporter.get('account_id')}")
        
        # Dates
        print(f"\nDates:")
        print(f"  Start Date: {issue_details.get('start_date')}")
        print(f"  Due Date: {issue_details.get('due_date')}")
        
        # Description (truncated)
        description = issue_details.get('description', '')
        if description:
            print(f"\nDescription: {description[:150]}...")
        else:
            print(f"\nDescription: (empty)")
        
        # Epic info
        epic_key = issue_details.get('epic_key')
        epic_name = issue_details.get('epic_name')
        if epic_key:
            print(f"\nEpic: {epic_name} ({epic_key})")
        
        # Parent info
        parent_key = issue_details.get('parent_key')
        if parent_key:
            print(f"Parent: {parent_key}")
        
        # Labels and components
        labels = issue_details.get('labels', [])
        components = issue_details.get('components', [])
        if labels:
            print(f"\nLabels: {', '.join(labels)}")
        if components:
            print(f"Components: {', '.join(components)}")
        
        # Comments
        comments = issue_details.get('comments', [])
        if comments:
            print(f"\nComments ({len(comments)}):")
            for i, comment in enumerate(comments[:3], 1):  # Show first 3 comments
                author = comment.get('author', {})
                print(f"  {i}. By {author.get('display_name')} on {comment.get('created')}")
                body = comment.get('body', '')
                print(f"     {body[:80]}...")
            if len(comments) > 3:
                print(f"  ... and {len(comments) - 3} more comments")
        else:
            print(f"\nComments: None")
        
        # Story points
        story_points = issue_details.get('story_points')
        if story_points:
            print(f"\nStory Points: {story_points}")
        
        return True
    except Exception as e:
        print(f"\n✗ Error getting issue details: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def test_jira_get_all_users():
    """Test getting all users for a project."""
    print("\n" + "="*60)
    print("Testing JiraGetAllUsersTool")
    print("="*60)

    tool = JiraGetAllUsersTool()

    # TODO: Replace with your test project key
    project_key = "MH"  # Change this to a valid project key

    print(f"\nGetting users for project: {project_key}")

    try:
        users = tool._run(project_key=project_key)
        print(f"\nFound {len(users)} users assignable to the project")

        # Display first 5 users as a sample
        print("\nSample users (first 5):")
        for user_map in users[:5]:
            for account_id, display_name in user_map.items():
                print(f"  {display_name} ({account_id})")

        if len(users) > 5:
            print(f"\n  ... and {len(users) - 5} more users")

        return True
    except Exception as e:
        print(f"\n- Error getting users: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def test_jira_get_all_sprints():
    """Test retrieving all sprints for a project."""
    print("\n" + "="*60)
    print("Testing JiraGetAllSprintsTool")
    print("="*60)

    tool = JiraGetAllSprintsTool()

    # TODO: Replace with your test project key
    project_key = "MH"  # Change this to a valid project key

    print(f"\nGetting sprints for project: {project_key}")

    try:
        sprints = tool._run(project_key=project_key)
        print(f"\nFound {len(sprints)} sprints across project boards")

        print("\nSample sprints (first 5):")
        for sprint_name, sprint_info in list(sprints.items())[:5]:
            print(f"  {sprint_name}:")
            print(f"    Sprint ID: {sprint_info.get('sprint_id')}")
            print(f"    State: {sprint_info.get('state')}")
            print(f"    Start: {sprint_info.get('start_date')}")
            print(f"    End: {sprint_info.get('end_date')}")
            print(f"    Issues: {len(sprint_info.get('issue_ids', []))}")

        return True
    except Exception as e:
        print(f"\n[ERROR] Error getting sprints: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def test_jira_get_sprint_issues():
    """Test retrieving all issues within a sprint."""
    print("\n" + "="*60)
    print("Testing JiraGetSprintIssuesTool")
    print("="*60)

    tool = JiraGetSprintIssuesTool()

    # TODO: Replace with a real sprint ID from your Jira.
    sprint_id = 1

    print(f"\nGetting issues for sprint ID: {sprint_id}")

    try:
        sprint_issues = tool._run(sprint_id=sprint_id)
        issues = sprint_issues.get("issues", {})
        print(f"\nFound {len(issues)} issues in sprint {sprint_id}")

        print("\nSample issues (first 5):")
        for issue_id, info in list(issues.items())[:5]:
            print(f"  {issue_id} ({info.get('issue_key')} - {info.get('issue_type')}): {info.get('summary')}")
            print(f"    Assignee ID: {info.get('assignee_id')}")
            description = info.get('description', '')
            print(f"    Description: {description[:100]}...")

        return True
    except Exception as e:
        print(f"\n[ERROR] Error getting sprint issues: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def test_jira_move_issue_to_sprint():
    """Test moving an issue into a sprint."""
    print("\n" + "="*60)
    print("Testing JiraMoveIssueToSprintTool")
    print("="*60)

    tool = JiraMoveIssueToSprintTool()

    # TODO: Replace with a real sprint ID and issue key.
    sprint_id = 1
    issue_key = "MH-79"

    print(f"\nMoving issue {issue_key} to sprint {sprint_id}")

    try:
        result = tool._run(sprint_id=sprint_id, issue_key=issue_key)
        print("\n[OK] Issue moved successfully!")
        print(f"Sprint ID: {result.get('sprint_id')}")
        print(f"Issue Key: {result.get('issue_key')}")
        print(f"Message: {result.get('message')}")
        return True
    except Exception as e:
        print(f"\n[ERROR] Error moving issue to sprint: {e}")
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
    assignee = '5fcfd938e40b82006e36206f'
    # assignee = None
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


def test_jira_create_sprint():
    """Test creating a Jira sprint."""
    print("\n" + "="*60)
    print("Testing JiraCreateSprintTool")
    print("="*60)

    tool = JiraCreateSprintTool()

    project_key = "MH"
    sprint_start_date = "2025-12-01"
    sprint_end_date = "2025-12-14"
    sprint_name = "Automation Test Sprint"

    print(f"\nCreating sprint for project: {project_key}")
    print(f"Sprint Start Date: {sprint_start_date}")
    print(f"Sprint End Date: {sprint_end_date}")
    print(f"Sprint Name: {sprint_name}")

    try:
        result = tool._run(
            project_key=project_key,
            sprint_start_date=sprint_start_date,
            sprint_end_date=sprint_end_date,
            sprint_name=sprint_name,
        )
        print("\n[OK] Sprint created successfully!")
        print(f"Sprint ID: {result.get('sprint_id')}")
        print(f"Board ID: {result.get('origin_board_id')}")
        print(f"Board Name: {result.get('origin_board_name')}")
        return True
    except Exception as e:
        print(f"\n[ERROR] Error creating sprint: {e}")
        if hasattr(e, "response") and e.response is not None:
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
    results.append(("Add Comment", test_jira_add_comment()))
    
    # Test 2: Assign Issue
    results.append(("Assign Issue", test_jira_assign_issue()))
    
    # Test 3: Get User History
    results.append(("Get User History", test_jira_get_user_history()))

    # Test 4: Get Issue Details
    results.append(("Get Issue Details", test_jira_get_issue_details()))

    # Test 5: Get All Users
    results.append(("Get All Users", test_jira_get_all_users()))

    # Test 6: Get All Sprints
    results.append(("Get All Sprints", test_jira_get_all_sprints()))
    
    # Test 7: Get Sprint Issues
    results.append(("Get Sprint Issues", test_jira_get_sprint_issues()))

    # Test 8: Move Issue to Sprint
    results.append(("Move Issue to Sprint", test_jira_move_issue_to_sprint()))

    # Test 9: Create Issue
    results.append(("Create Issue", test_jira_create_issue()))
    
    # Test 10: Create Sprint
    results.append(("Create Sprint", test_jira_create_sprint()))
    
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

