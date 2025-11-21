import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# Environment variable loading
# Go up from tools/ -> jira_ai_assistant/ -> src/ -> jira_ai_assistant/ -> project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
ENV_LOCATIONS = [BASE_DIR / "jira_ai_assistant" / ".env", BASE_DIR / ".env"]


def _load_env_file(env_path: Path) -> None:
    """
    Load environment variables from a .env file if present.
    Existing environment values are left untouched so external config can override.
    """
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Strip optional surrounding quotes
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        if key and key not in os.environ:
            os.environ[key] = value


for env_file in ENV_LOCATIONS:
    _load_env_file(env_file)

JIRA_URL = os.getenv("JIRA_URL", "")
EMAIL = os.getenv("EMAIL", "")
API_KEY = os.getenv("API_KEY", "")


def _extract_text_from_adf(adf_content: Any) -> str:
    """
    Helper function to extract plain text from Atlassian Document Format (ADF).
    
    Args:
        adf_content: ADF content structure (dict or list)
    
    Returns:
        str: Plain text extracted from ADF
    """
    if not adf_content:
        return ""
    
    if isinstance(adf_content, str):
        return adf_content
    
    if isinstance(adf_content, dict):
        if adf_content.get("type") == "text":
            return adf_content.get("text", "")
        if "content" in adf_content:
            return _extract_text_from_adf(adf_content["content"])
    
    if isinstance(adf_content, list):
        return " ".join(_extract_text_from_adf(item) for item in adf_content)
    
    return ""


def _format_date(date_str: str) -> str:
    """
    Helper function to format ISO date string to DD/MM/YYYY format.
    
    Args:
        date_str: ISO date string (e.g., '2025-08-17T10:00:00.000+0000')
    
    Returns:
        str: Formatted date string (e.g., '17/08/2025')
    """
    if not date_str:
        return ""
    
    try:
        # Parse ISO format date
        dt = datetime.fromisoformat(date_str.replace('+0000', '+00:00').replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y")
    except (ValueError, AttributeError):
        return date_str


# Tool 1: JiraAddCommentTool
class JiraAddCommentToolInput(BaseModel):
    """Input schema for JiraAddCommentTool."""
    issue_key: str = Field(..., description="The key of the Jira issue (e.g., 'PROJ-123')")
    body: str = Field(..., description="The comment text to add")


class JiraAddCommentTool(BaseTool):
    name: str = "jira_add_comment"
    description: str = (
        "Adds a comment to a Jira issue. Used for delayed tasks follow-up, clarifications, and risk notes."
    )
    args_schema: Type[BaseModel] = JiraAddCommentToolInput

    def _run(self, issue_key: str, body: str) -> dict:
        """
        Adds a comment to a Jira issue.
        
        Args:
            issue_key: The key of the Jira issue (e.g., 'PROJ-123')
            body: The comment text to add
        
        Returns:
            dict: The response from the Jira API containing the created comment
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        # Remove trailing slash from URL if present
        jira_url = JIRA_URL.rstrip('/')
        
        # Jira REST API endpoint for adding a comment
        endpoint = f"{jira_url}/rest/api/3/issue/{issue_key}/comment"
        
        # Prepare authentication (Basic Auth with email and API key)
        auth = (EMAIL, API_KEY)
        
        # Prepare the request payload
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": body
                            }
                        ]
                    }
                ]
            }
        }
        
        # Set headers
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Make the API request
        response = requests.post(
            endpoint,
            json=payload,
            auth=auth,
            headers=headers
        )
        
        # Raise an exception if the request failed
        response.raise_for_status()
        
        # Return the response JSON
        return response.json()


# Tool 2: JiraAssignIssueTool
class JiraAssignIssueToolInput(BaseModel):
    """Input schema for JiraAssignIssueTool."""
    issue_key: str = Field(..., description="The key of the Jira issue (e.g., 'PROJ-123')")
    assignee_account_id: str = Field(..., description="The account ID of the person to assign the issue to")


class JiraAssignIssueTool(BaseTool):
    name: str = "jira_assign_issue"
    description: str = (
        "Assigns a Jira issue (Task, Story, or Subtask) to a person. Used after skill-based assignment selection."
    )
    args_schema: Type[BaseModel] = JiraAssignIssueToolInput

    def _run(self, issue_key: str, assignee_account_id: str) -> dict:
        """
        Assigns a Jira issue (Task, Story, or Subtask) to a person.
        
        Args:
            issue_key: The key of the Jira issue (e.g., 'PROJ-123')
            assignee_account_id: The account ID of the person to assign the issue to
        
        Returns:
            dict: The response from the Jira API (usually empty on success)
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        # Remove trailing slash from URL if present
        jira_url = JIRA_URL.rstrip('/')
        
        # Jira REST API endpoint for assigning an issue
        endpoint = f"{jira_url}/rest/api/3/issue/{issue_key}/assignee"
        
        # Prepare authentication (Basic Auth with email and API key)
        auth = (EMAIL, API_KEY)
        
        # Prepare the request payload
        payload = {
            "accountId": assignee_account_id
        }
        
        # Set headers
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Make the API request
        response = requests.put(
            endpoint,
            json=payload,
            auth=auth,
            headers=headers
        )
        
        # Raise an exception if the request failed
        response.raise_for_status()
        
        # Return the response JSON (usually empty on success)
        return response.json() if response.text else {}


# Tool 3: JiraGetUserHistoryTool
class JiraGetUserHistoryToolInput(BaseModel):
    """Input schema for JiraGetUserHistoryTool."""
    account_id: str = Field(..., description="The account ID of the user")


class JiraGetUserHistoryTool(BaseTool):
    name: str = "jira_get_user_history"
    description: str = (
        "Gets all history of a user, containing assigned tasks, descriptions, status, dates, work logs, etc. "
        "Returns aggregated stats for all issues assigned to them including start_date, end_date, status, "
        "issue_type, description, due_date, work_log, and other useful information."
    )
    args_schema: Type[BaseModel] = JiraGetUserHistoryToolInput

    def _run(self, account_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Gets all history of a user, containing assigned tasks, descriptions, status, dates, work logs, etc.
        
        Args:
            account_id: The account ID of the user
        
        Returns:
            dict: Dictionary where outer key is issue_key (e.g., 'MH-8') and inner dict contains:
                - issue_type: Type of issue (Story, Task, Bug, Sub-task)
                - description: Issue description
                - status: Current status (TODO, Ongoing, Done, etc.)
                - start_date: Start/created date (DD/MM/YYYY)
                - due_date: Due date (DD/MM/YYYY)
                - work_log: Work log information
                - summary: Issue summary/title
                - priority: Issue priority
                - created: Original creation date
                - updated: Last update date
                - assignee: Assignee information
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        jira_url = JIRA_URL.rstrip('/')
        auth = (EMAIL, API_KEY)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        all_issues = {}
        start_at = 0
        max_results = 100
        
        # Search for all issues assigned to the user (with pagination)
        while True:
            # Using the new /rest/api/3/search/jql endpoint as required
            search_endpoint = f"{jira_url}/rest/api/3/search/jql"
            
            # JQL query - try different formats
            # First try without accountId() function (most common format)
            jql_query = f'assignee = "{account_id}" ORDER BY updated DESC'
            
            # Try GET method first with query parameters
            params = {
                "jql": jql_query,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "summary,description,status,issuetype,created,updated,duedate,priority,assignee,key"
            }
            
            response = requests.get(
                search_endpoint,
                params=params,
                auth=auth,
                headers=headers
            )
            
            # If GET fails, try POST with body
            if response.status_code == 405 or response.status_code == 400:
                # Prepare request payload for POST
                payload = {
                    "jql": jql_query,
                    "startAt": start_at,
                    "maxResults": max_results,
                    "fields": ["summary", "description", "status", "issuetype", "created", "updated", "duedate", "priority", "assignee", "key"]
                }
                
                response = requests.post(
                    search_endpoint,
                    json=payload,
                    auth=auth,
                    headers=headers
                )
            response.raise_for_status()
            search_result = response.json()
            
            issues = search_result.get("issues", [])
            if not issues:
                break
            
            # Process each issue
            for issue in issues:
                issue_key = issue.get("key")
                fields = issue.get("fields", {})
                
                # Extract basic information
                issue_type = fields.get("issuetype", {}).get("name", "Unknown")
                status = fields.get("status", {}).get("name", "Unknown")
                summary = fields.get("summary", "")
                priority = fields.get("priority", {}).get("name", "Unknown")
                created = fields.get("created", "")
                updated = fields.get("updated", "")
                due_date = fields.get("duedate", "")
                
                # Extract description (handle ADF format)
                description_field = fields.get("description")
                description = ""
                if description_field:
                    if isinstance(description_field, dict):
                        description = _extract_text_from_adf(description_field)
                    else:
                        description = str(description_field)
                
                # Get work log for this issue
                work_log_text = ""
                try:
                    worklog_endpoint = f"{jira_url}/rest/api/3/issue/{issue_key}/worklog"
                    worklog_response = requests.get(
                        worklog_endpoint,
                        auth=auth,
                        headers=headers
                    )
                    if worklog_response.status_code == 200:
                        worklog_data = worklog_response.json()
                        worklogs = worklog_data.get("worklogs", [])
                        if worklogs:
                            work_log_entries = []
                            for wl in worklogs:
                                author = wl.get("author", {}).get("displayName", "Unknown")
                                time_spent = wl.get("timeSpent", "")
                                started = wl.get("started", "")
                                comment = wl.get("comment", "")
                                comment_text = _extract_text_from_adf(comment) if comment else ""
                                work_log_entries.append(
                                    f"{author}: {time_spent} on {_format_date(started)}"
                                    + (f" - {comment_text}" if comment_text else "")
                                )
                            work_log_text = "; ".join(work_log_entries)
                except requests.exceptions.RequestException:
                    # If work log fetch fails, continue without it
                    pass
                
                # Format dates
                start_date = _format_date(created)
                formatted_due_date = _format_date(due_date) if due_date else ""
                
                # Build issue information dictionary
                all_issues[issue_key] = {
                    "issue_type": issue_type,
                    "description": description,
                    "status": status,
                    "start_date": start_date,
                    "due_date": formatted_due_date,
                    "work_log": work_log_text,
                    "summary": summary,
                    "priority": priority,
                    "created": created,
                    "updated": updated,
                    "assignee": fields.get("assignee", {}).get("displayName", "Unknown")
                }
            
            # Check if there are more results
            start_at += len(issues)
            if start_at >= search_result.get("total", 0):
                break
        
        return all_issues
