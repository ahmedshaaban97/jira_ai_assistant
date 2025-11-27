import os
from datetime import datetime
from typing import Any, Dict, Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from .utils import _extract_text_from_adf, _format_date, load_jira_env

# Load environment variables
load_jira_env()

JIRA_URL = os.getenv("JIRA_URL", "")
EMAIL = os.getenv("EMAIL", "")
API_KEY = os.getenv("API_KEY", "")


# Tool: JiraAddCommentTool
class JiraAddCommentToolInput(BaseModel):
    """Input schema for JiraAddCommentTool."""
    issue_key: str = Field(..., description="The Jira issue key as a string (e.g., 'MH-9')")
    body: str = Field(..., description="The comment text to add as a plain string (e.g., 'This task is blocked by infrastructure work')")


class JiraAddCommentTool(BaseTool):
    name: str = "jira_add_comment"
    description: str = (
        "Adds a plain-text comment to a Jira issue. Use this to document risks, clarifications, blockers, "
        "or follow-up notes on tasks. Essential for explaining capacity constraints or timeline concerns."
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


# Tool: JiraAssignIssueTool
class JiraAssignIssueToolInput(BaseModel):
    """Input schema for JiraAssignIssueTool."""
    issue_key: str = Field(..., description="The Jira issue key as a string (e.g., 'MH-9')")
    assignee_account_id: str = Field(..., description="The assignee's Jira account ID as a string, NOT display name (e.g., '5fcfd938e40b82006e36206f'). Obtain from jira_get_all_users tool.")


class JiraAssignIssueTool(BaseTool):
    name: str = "jira_assign_issue"
    description: str = (
        "Assigns a Jira issue (Task, Story, Bug, or Sub-task) to a team member by their account ID. "
        "Use this after matching skills from CVs and Jira history. Always use account ID, never display names."
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


# Tool: JiraGetAllUsersTool
class JiraGetAllUsersToolInput(BaseModel):
    """Input schema for JiraGetAllUsersTool."""
    project_key: str = Field(..., description="The Jira project key as a string (e.g., 'MH')")


class JiraGetAllUsersTool(BaseTool):
    name: str = "jira_get_all_users"
    description: str = (
        "Retrieves all assignable users in a Jira project. Returns a list of dictionaries mapping account IDs "
        "to display names (e.g., [{'5fcfd938e40b82006e36206f': 'Ahmed Shaaban'}]). Use this to get valid "
        "account IDs before assigning issues. Essential for planning assignments."
    )
    args_schema: Type[BaseModel] = JiraGetAllUsersToolInput

    def _run(self, project_key: str) -> list:
        """
        Gets all users in a given project.

        Args:
            project_key: The Jira project key (e.g., 'MH')

        Returns:
            list: List of dictionaries where each dictionary contains a single key-value pair of accountId: displayName

        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        jira_url = JIRA_URL.rstrip('/')
        auth = (EMAIL, API_KEY)
        headers = {
            "Accept": "application/json"
        }

        # Jira endpoint for users assignable to a project
        endpoint = f"{jira_url}/rest/api/3/user/assignable/search"

        users = []
        seen_accounts = set()
        start_at = 0
        max_results = 100

        # Paginate through all assignable users for the project
        while True:
            params = {
                "project": project_key,
                "startAt": start_at,
                "maxResults": max_results
            }
            response = requests.get(
                endpoint,
                params=params,
                auth=auth,
                headers=headers
            )
            response.raise_for_status()
            batch = response.json()

            if not batch:
                break

            for user in batch:
                account_id = user.get("accountId")
                display_name = user.get("displayName", "")
                if account_id and account_id not in seen_accounts:
                    users.append({account_id: display_name})
                    seen_accounts.add(account_id)

            if len(batch) < max_results:
                break
            start_at += max_results

        return users


# Tool: JiraGetUserHistoryTool
class JiraGetUserHistoryToolInput(BaseModel):
    """Input schema for JiraGetUserHistoryTool."""
    account_id: str = Field(..., description="The user's Jira account ID as a string (e.g., '5fcfd938e40b82006e36206f'). Obtain from jira_get_all_users tool.")


class JiraGetUserHistoryTool(BaseTool):
    name: str = "jira_get_user_history"
    description: str = (
        "Retrieves complete work history for a user including all assigned issues, their types, status, dates, "
        "work logs, and descriptions. Returns dict keyed by issue_key (e.g., 'MH-8') with issue_type, status, "
        "start_date, due_date, work_log, summary, priority. Use this to assess user skills, throughput, and "
        "current workload before making assignments."
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


# Tool: JiraGetAllEpicsTool
class JiraGetAllEpicsToolInput(BaseModel):
    """Input schema for JiraGetAllEpicsTool."""
    project_key: str = Field(..., description="The Jira project key as a string (e.g., 'MH')")
    


class JiraGetAllEpicsTool(BaseTool):
    name: str = "jira_get_all_epics"
    description: str = (
        "Retrieves all epics in a project with comprehensive details. Returns list of dicts containing "
        "epic_key (e.g., 'MH-7'), epic_summary, epic_description, epic_created_at, epic_start_date, "
        "epic_due_date, and epic_status. Use this to understand epic scope and timelines before planning work."
    )
    args_schema: Type[BaseModel] = JiraGetAllEpicsToolInput

    def _run(self, project_key: str) -> list:
        """
        Gets all epics for a given project key.
        
        Args:
            project_key: The Jira project key (e.g., 'MH')
        
        Returns:
            list: List of dictionaries containing epic information:
                - epic_summary: Epic summary/title
                - epic_key: Epic key (e.g., 'MH-1')
                - epic_description: Epic description (plain text)
                - epic_created_at: Epic creation date
                - epic_start_date: Epic start date (if exists)
                - epic_due_date: Epic due date (if exists)
                - epic_status: Epic status (if exists)
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        jira_url = JIRA_URL.rstrip('/')
        auth = (EMAIL, API_KEY)
        headers = {
            "Accept": "application/json"
        }
        
        # Step 1: Search for all epics in the project
        search_endpoint = f"{jira_url}/rest/api/3/search/jql"
        query = {
            'jql': f'project = {project_key} AND issuetype = Epic'
        }
        
        response = requests.get(
            search_endpoint,
            headers=headers,
            params=query,
            auth=auth
        )
        response.raise_for_status()
        epic_data = response.json()
        epic_ids = [issue['id'] for issue in epic_data.get('issues', [])]
        
        # Step 2: Get full details for each epic
        all_epics = []
        for epic_id in epic_ids:
            issue_endpoint = f"{jira_url}/rest/api/3/issue/{epic_id}"
            epic_response = requests.get(
                issue_endpoint,
                headers=headers,
                auth=auth
            )
            epic_response.raise_for_status()
            epic_details = epic_response.json()
            
            # Extract fields
            fields = epic_details.get('fields', {})
            
            # Extract description (handle ADF format)
            description = ""
            description_field = fields.get('description')
            if description_field:
                if isinstance(description_field, dict):
                    description = _extract_text_from_adf(description_field)
                else:
                    description = str(description_field)
            
            # Extract status
            status = None
            status_field = fields.get('status')
            if status_field:
                status = status_field.get('name')
            
            # Build epic info dictionary
            epic_info = {
                'epic_summary': fields.get('summary', ''),
                'epic_key': epic_details.get('key', ''),
                'epic_description': description,
                'epic_created_at': fields.get('created', ''),
                'epic_start_date': fields.get('customfield_10014', None),  # Common epic start date field
                'epic_due_date': fields.get('duedate', None),
                'epic_status': status
            }
            
            all_epics.append(epic_info)
        
        return all_epics


# Tool: JiraGetIssueDetailsTool
class JiraGetIssueDetailsToolInput(BaseModel):
    """Input schema for JiraGetIssueDetailsTool."""
    issue_key: str = Field(..., description="The Jira issue key as a string (e.g., 'MH-9')")


class JiraGetIssueDetailsTool(BaseTool):
    name: str = "jira_get_issue_details"
    description: str = (
        "Retrieves comprehensive details for a specific issue. Returns dict with issue_key, issue_summary, "
        "issue_description, issue_type, issue_status, issue_created_at, issue_updated_at, issue_due_date, "
        "issue_start_date, issue_assignee, issue_assignee_id, issue_reporter, issue_priority, epic_key, "
        "parent_key, story_points, labels, and components. Use to inspect existing work before updating or planning."
    )
    args_schema: Type[BaseModel] = JiraGetIssueDetailsToolInput

    def _run(self, issue_key: str) -> Dict[str, Any]:
        """
        Gets detailed information for a specific Jira issue.
        
        Args:
            issue_key: The Jira issue key or ID (e.g., 'PROJ-123' or '10038')
        
        Returns:
            dict: Dictionary containing detailed issue information:
                - issue_key: Issue key (e.g., 'PROJ-123')
                - issue_id: Issue ID
                - issue_summary: Issue summary/title
                - issue_description: Issue description (plain text)
                - issue_type: Issue type (Story, Task, Bug, etc.)
                - issue_status: Issue status
                - issue_created_at: Issue creation date
                - issue_updated_at: Issue last updated date
                - issue_due_date: Issue due date (if exists)
                - issue_start_date: Issue start date (if exists)
                - issue_assignee: Assignee name (if exists)
                - issue_assignee_id: Assignee account ID (if exists)
                - issue_reporter: Reporter name
                - issue_priority: Priority (if exists)
                - epic_key: Epic key if linked to an epic
                - parent_key: Parent issue key (for sub-tasks)
                - story_points: Story points (if exists)
                - labels: List of labels
                - components: List of component names
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        jira_url = JIRA_URL.rstrip('/')
        auth = (EMAIL, API_KEY)
        headers = {
            "Accept": "application/json"
        }
        
        # Get issue details
        endpoint = f"{jira_url}/rest/api/3/issue/{issue_key}"
        response = requests.get(
            endpoint,
            headers=headers,
            auth=auth
        )
        response.raise_for_status()
        issue_data = response.json()
        
        # Extract fields
        fields = issue_data.get('fields', {})
        
        # Extract description (handle ADF format)
        description = ""
        description_field = fields.get('description')
        if description_field:
            if isinstance(description_field, dict):
                description = _extract_text_from_adf(description_field)
            else:
                description = str(description_field)
        
        # Extract epic key if linked
        epic_key_linked = None
        epic_link_field = fields.get('customfield_10014')  # Common epic link field
        if epic_link_field:
            epic_key_linked = epic_link_field
        
        # Extract parent key (for sub-tasks)
        parent_key = None
        parent_field = fields.get('parent')
        if parent_field:
            parent_key = parent_field.get('key')
        
        # Extract start date (may be custom field)
        start_date = None
        start_date_field = fields.get('customfield_10015')  # Common start date field
        if start_date_field:
            start_date = _format_date(start_date_field) if start_date_field else None
        
        # Extract story points (may be custom field)
        story_points = None
        story_points_field = fields.get('customfield_10016')  # Common story points field
        if story_points_field:
            story_points = story_points_field
        
        # Extract labels
        labels = fields.get('labels', [])
        
        # Extract components
        components = [comp.get('name') for comp in fields.get('components', [])]
        
        # Extract assignee info
        assignee_name = None
        assignee_id = None
        assignee = fields.get('assignee')
        if assignee:
            assignee_name = assignee.get('displayName')
            assignee_id = assignee.get('accountId')
        
        # Build issue info dictionary
        issue_info = {
            'issue_key': issue_data.get('key'),
            'issue_id': issue_data.get('id'),
            'issue_summary': fields.get('summary', ''),
            'issue_description': description,
            'issue_type': fields.get('issuetype', {}).get('name', 'Unknown'),
            'issue_status': fields.get('status', {}).get('name', 'Unknown'),
            'issue_created_at': fields.get('created', ''),
            'issue_updated_at': fields.get('updated', ''),
            'issue_due_date': _format_date(fields.get('duedate')) if fields.get('duedate') else None,
            'issue_start_date': start_date,
            'issue_assignee': assignee_name,
            'issue_assignee_id': assignee_id,
            'issue_reporter': fields.get('reporter', {}).get('displayName', 'Unknown') if fields.get('reporter') else 'Unknown',
            'issue_priority': fields.get('priority', {}).get('name', None) if fields.get('priority') else None,
            'epic_key': epic_key_linked,
            'parent_key': parent_key,
            'story_points': story_points,
            'labels': labels,
            'components': components
        }
        
        return issue_info


# Tool: JiraGetAllIssuesWithDetailsTool
class JiraGetAllIssuesWithDetailsToolInput(BaseModel):
    """Input schema for JiraGetAllIssuesWithDetailsTool."""
    project_key: str = Field(..., description="The Jira project key as a string (e.g., 'MH')")
    epic_key: str = Field("", description="Optional epic key as a string to filter issues (e.g., 'MH-7', 'PROJ-7'). If empty string, returns all non-epic issues in project.")


class JiraGetAllIssuesWithDetailsTool(BaseTool):
    name: str = "jira_get_all_issues_with_details"
    description: str = (
        "Retrieves all issues in a project or epic with full details. Returns list of dicts with same fields "
        "as jira_get_issue_details. Optionally filter by epic_key to see only issues linked to that epic. "
        "Essential for understanding existing workload, assignments, and timeline conflicts before planning."
    )
    args_schema: Type[BaseModel] = JiraGetAllIssuesWithDetailsToolInput

    def _run(self, project_key: str, epic_key: str = None) -> list:
        """
        Gets all issues with full details for a given project key, optionally filtered by epic.
        
        Args:
            project_key: The Jira project key (e.g., 'PROJ')
            epic_key: Optional epic key to filter issues (e.g., 'PROJ-7'). If None, returns all issues.
        
        Returns:
            list: List of dictionaries containing detailed issue information for each issue
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        jira_url = JIRA_URL.rstrip('/')
        auth = (EMAIL, API_KEY)
        headers = {
            "Accept": "application/json"
        }
        
        # Build JQL query
        if epic_key:
            # Filter by project and epic
            jql_query = f'project = {project_key} AND "Epic Link" = {epic_key}'
        else:
            # Get all issues in project (excluding epics)
            jql_query = f'project = {project_key} AND issuetype != Epic'
        
        # Step 1: Search for issue keys
        search_endpoint = f"{jira_url}/rest/api/3/search/jql"
        query = {
            'jql': jql_query,
            'fields': 'key'  # Only get keys first
        }
        
        all_issue_keys = []
        start_at = 0
        max_results = 100
        
        # Handle pagination to get all issue keys
        while True:
            query['startAt'] = start_at
            query['maxResults'] = max_results
            
            response = requests.get(
                search_endpoint,
                headers=headers,
                params=query,
                auth=auth
            )
            response.raise_for_status()
            search_data = response.json()
            
            issues = search_data.get('issues', [])
            if not issues:
                break
            
            # Collect issue keys
            for issue in issues:
                all_issue_keys.append(issue.get('key'))
            
            # Check if there are more results
            total = search_data.get('total', 0)
            start_at += len(issues)
            if start_at >= total:
                break
        
        # Step 2: Get full details for each issue
        all_issues_details = []
        for issue_key in all_issue_keys:
            # Get issue details using the endpoint
            endpoint = f"{jira_url}/rest/api/3/issue/{issue_key}"
            issue_response = requests.get(
                endpoint,
                headers=headers,
                auth=auth
            )
            issue_response.raise_for_status()
            issue_data = issue_response.json()
            
            # Extract fields
            fields = issue_data.get('fields', {})
            
            # Extract description (handle ADF format)
            description = ""
            description_field = fields.get('description')
            if description_field:
                if isinstance(description_field, dict):
                    description = _extract_text_from_adf(description_field)
                else:
                    description = str(description_field)
            
            # Extract epic key if linked
            epic_key_linked = None
            epic_link_field = fields.get('customfield_10014')
            if epic_link_field:
                epic_key_linked = epic_link_field
            
            # Extract parent key (for sub-tasks)
            parent_key = None
            parent_field = fields.get('parent')
            if parent_field:
                parent_key = parent_field.get('key')
            
            # Extract start date
            start_date = None
            start_date_field = fields.get('customfield_10015')
            if start_date_field:
                start_date = _format_date(start_date_field) if start_date_field else None
            
            # Extract story points
            story_points = None
            story_points_field = fields.get('customfield_10016')
            if story_points_field:
                story_points = story_points_field
            
            # Extract labels and components
            labels = fields.get('labels', [])
            components = [comp.get('name') for comp in fields.get('components', [])]
            
            # Extract assignee info
            assignee_name = None
            assignee_id = None
            assignee = fields.get('assignee')
            if assignee:
                assignee_name = assignee.get('displayName')
                assignee_id = assignee.get('accountId')
            
            # Build issue info dictionary
            issue_info = {
                'issue_key': issue_data.get('key'),
                'issue_id': issue_data.get('id'),
                'issue_summary': fields.get('summary', ''),
                'issue_description': description,
                'issue_type': fields.get('issuetype', {}).get('name', 'Unknown'),
                'issue_status': fields.get('status', {}).get('name', 'Unknown'),
                'issue_created_at': fields.get('created', ''),
                'issue_updated_at': fields.get('updated', ''),
                'issue_due_date': _format_date(fields.get('duedate')) if fields.get('duedate') else None,
                'issue_start_date': start_date,
                'issue_assignee': assignee_name,
                'issue_assignee_id': assignee_id,
                'issue_reporter': fields.get('reporter', {}).get('displayName', 'Unknown') if fields.get('reporter') else 'Unknown',
                'issue_priority': fields.get('priority', {}).get('name', None) if fields.get('priority') else None,
                'epic_key': epic_key_linked,
                'parent_key': parent_key,
                'story_points': story_points,
                'labels': labels,
                'components': components
            }
            
            all_issues_details.append(issue_info)
        
        return all_issues_details


# Tool: JiraCreateIssueTool
class JiraCreateIssueToolInput(BaseModel):
    """Input schema for JiraCreateIssueTool."""
    project_key: str = Field(..., description="The project key as a string (e.g., 'MH')")
    summary: str = Field(..., description="The issue title as a string (e.g., 'Implement user authentication')")
    description: str = Field(..., description="The issue description as plain text, including acceptance criteria (e.g., 'Build login endpoint with JWT tokens')")
    issue_type: str = Field(default="Task", description="The issue type as a string: 'Task', 'Story', 'Bug', or 'Sub-task' (default: 'Task')")
    epic_key: str = Field("", description="The epic key to link to as a string (e.g., 'MH-7'). Ignored for Sub-tasks (they inherit from parent).")
    parent_key: str = Field("", description="The parent issue key for Sub-tasks as a string (e.g., 'MH-10'). Required only for Sub-tasks.")
    start_date: str = Field("", description="Start date as string in YYYY-MM-DD format (e.g., '2025-12-01'). Optional.")
    due_date: str = Field("", description="Due date as string in YYYY-MM-DD format (e.g., '2025-12-05'). Optional.")
    assignee: str = Field("", description="Assignee account ID as a string (e.g., '5fcfd938e40b82006e36206f') not display name. Use jira_get_all_users to get IDs. Optional.")
    story_points: int = Field(None, description="Story points as an integer (e.g., 1, 2, 3, 5, 8). Optional.")


class JiraCreateIssueTool(BaseTool):
    name: str = "jira_create_issue"
    description: str = (
        "Creates a new Jira issue with full details. Supports Task, Story, Bug, or Sub-task types. Links to epics "
        "automatically (Sub-tasks inherit epic from parent). Sets assignee by account ID, dates (YYYY-MM-DD), and "
        "story points. Returns issue_key and issue_id. Use this to execute backlog plans."
    )
    args_schema: Type[BaseModel] = JiraCreateIssueToolInput

    def _run(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        epic_key: str = None,
        parent_key: str = None,
        start_date: str = None,
        due_date: str = None,
        assignee: str = None,
        story_points: int = None
    ) -> Dict[str, str]:
        """
        Creates a new Jira issue and links it to an Epic (if epic_key is provided).
        For sub-tasks, the epic is inherited from the parent issue automatically.
        
        Args:
            project_key: The project key (e.g., 'PROJ')
            summary: The issue summary/title
            description: The issue description (plain text)
            issue_type: The type of issue (e.g., 'Task', 'Story', 'Bug', 'Sub-task')
            epic_key: The epic key to link the issue to (e.g., 'PROJ-7'). Ignored for sub-tasks.
            parent_key: The parent issue key for sub-tasks (e.g., 'PROJ-10')
            start_date: Start date in format 'YYYY-MM-DD'
            due_date: Due date in format 'YYYY-MM-DD'
            assignee: Assignee account ID
            story_points: Story points value
        
        Returns:
            dict: Dictionary containing:
                - issue_key: The created issue key (e.g., 'PROJ-123')
                - issue_id: The created issue ID
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        jira_url = JIRA_URL.rstrip('/')
        auth = (EMAIL, API_KEY)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Build the core payload
        fields = {
            "project": {
                "key": project_key
            },
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            },
            "issuetype": {
                "name": issue_type
            }
        }
        
        # Set Organizations field (customfield_10002) to empty array as it's required
        fields["customfield_10002"] = []
        
        # IMPORTANT: Sub-tasks automatically inherit the epic from their parent
        # So we only set epic link for regular issues (not sub-tasks)
        if epic_key and not parent_key:
            # Only link to epic for regular issues (Tasks, Stories, Bugs - NOT sub-tasks)
            fields["customfield_10014"] = epic_key  # Common epic link field
        
        # If creating a sub-task, set the parent
        if parent_key:
            # Note: Sub-tasks require a 'parent' field and will automatically inherit the epic
            fields["parent"] = {"key": parent_key}
        
        # Add assignee
        if assignee:
            fields["assignee"] = {"accountId": assignee}
        
        # Add due date (standard Jira field)
        if due_date:
            fields["duedate"] = due_date
        
        # Add start date (may be custom field)
        if start_date:
            fields["customfield_10015"] = start_date  # Common start date field
        
        # Add story points (may be custom field)
        if story_points is not None:
            fields["customfield_10016"] = story_points  # Common story points field
        
        # Create the issue
        endpoint = f"{jira_url}/rest/api/3/issue"
        response = requests.post(
            endpoint,
            json={"fields": fields},
            headers=headers,
            auth=auth
        )
        response.raise_for_status()
        
        response_data = response.json()
        return {
            "issue_key": response_data.get("key"),
            "issue_id": response_data.get("id")
        }


class JiraCreateSprintToolInput(BaseModel):
    """Input schema for JiraCreateSprintTool."""
    project_key: str = Field(..., description="The Jira project key as a string (e.g., 'MH').")
    sprint_start_date: str = Field(..., description="Sprint start date in YYYY-MM-DD format (e.g., '2025-12-01').")
    sprint_end_date: str = Field(..., description="Sprint end date in YYYY-MM-DD format (e.g., '2025-12-14').")
    sprint_name: str = Field("", description="Optional sprint name. Defaults to '<PROJECT> Sprint <start_date>'.")


class JiraCreateSprintTool(BaseTool):
    name: str = "jira_create_sprint"
    description: str = (
        "Creates a new sprint for the given project on its Scrum board. Provide the project key and sprint "
        "start/end dates (YYYY-MM-DD). Returns metadata for the newly created sprint."
    )
    args_schema: Type[BaseModel] = JiraCreateSprintToolInput

    @staticmethod
    def _format_sprint_datetime(date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Sprint dates must use YYYY-MM-DD format.") from exc

    def _run(
        self,
        project_key: str,
        sprint_start_date: str,
        sprint_end_date: str,
        sprint_name: str = ""
    ) -> Dict[str, Any]:
        """
        Creates a new sprint for the first scrum board tied to the provided project key.

        Args:
            project_key: The Jira project key (e.g., 'PROJ')
            sprint_start_date: Sprint start date (YYYY-MM-DD)
            sprint_end_date: Sprint end date (YYYY-MM-DD)
            sprint_name: Optional sprint name

        Returns:
            dict: Dictionary containing sprint metadata including sprint_id, sprint_name,
                  project_key, sprint_start_date, sprint_end_date, and board info.

        Raises:
            ValueError: If no boards exist for the project or the date format is invalid.
            requests.exceptions.RequestException: If the API request fails.
        """
        jira_url = JIRA_URL.rstrip('/')
        auth = (EMAIL, API_KEY)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        start_dt = self._format_sprint_datetime(sprint_start_date)
        end_dt = self._format_sprint_datetime(sprint_end_date)

        if end_dt <= start_dt:
            raise ValueError("sprint_end_date must be after sprint_start_date.")

        start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%S.000+0000")
        end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%S.000+0000")

        # Discover available boards for the project
        board_endpoint = f"{jira_url}/rest/agile/1.0/board"
        max_results = 50
        start_at = 0
        boards = []

        while True:
            params = {
                "projectKeyOrId": project_key,
                "startAt": start_at,
                "maxResults": max_results
            }
            board_response = requests.get(
                board_endpoint,
                params=params,
                headers=headers,
                auth=auth
            )
            board_response.raise_for_status()
            board_data = board_response.json()
            values = board_data.get("values", [])
            boards.extend(values)

            if board_data.get("isLast") is True or len(values) < max_results:
                break
            start_at += max_results

        if not boards:
            raise ValueError(f"No boards found for project '{project_key}'.")

        # Prefer scrum boards, otherwise fall back to the first available board
        selected_board = next(
            (board for board in boards if (board.get("type") or "").lower() == "scrum"),
            boards[0]
        )
        board_id = selected_board.get("id")
        if board_id is None:
            raise ValueError(f"Could not determine a valid board ID for project '{project_key}'.")

        resolved_name = sprint_name.strip() or f"{project_key.upper()} Sprint {start_dt.strftime('%Y-%m-%d')}"

        payload = {
            "name": resolved_name,
            "startDate": start_iso,
            "endDate": end_iso,
            "originBoardId": board_id
        }

        create_endpoint = f"{jira_url}/rest/agile/1.0/sprint"
        response = requests.post(
            create_endpoint,
            json=payload,
            headers=headers,
            auth=auth
        )
        response.raise_for_status()
        sprint_info = response.json()

        return {
            "sprint_id": sprint_info.get("id"),
            "sprint_name": sprint_info.get("name"),
            "project_key": project_key,
            "sprint_start_date": sprint_start_date,
            "sprint_end_date": sprint_end_date,
            "state": sprint_info.get("state"),
            "origin_board_id": sprint_info.get("originBoardId"),
            "origin_board_name": selected_board.get("name"),
            "self_url": sprint_info.get("self")
        }


class JiraGetAllSprintsToolInput(BaseModel):
    """Input schema for JiraGetAllSprintsTool."""
    project_key: str = Field(..., description="The Jira project key as a string (e.g., 'MH').")


class JiraGetAllSprintsTool(BaseTool):
    name: str = "jira_get_all_sprints"
    description: str = (
        "Lists every sprint linked to the project's boards. Returns a dict keyed by sprint name with start/end dates, "
        "state, board metadata, and the IDs/keys for all issues assigned to that sprint."
    )
    args_schema: Type[BaseModel] = JiraGetAllSprintsToolInput

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        if not date_str:
            return ""
        try:
            parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            return date_str

    @staticmethod
    def _get_boards(jira_url: str, project_key: str, headers: dict, auth: tuple) -> list:
        endpoint = f"{jira_url}/rest/agile/1.0/board"
        boards = []
        start_at = 0
        max_results = 50

        while True:
            params = {
                "projectKeyOrId": project_key,
                "startAt": start_at,
                "maxResults": max_results
            }
            response = requests.get(endpoint, params=params, headers=headers, auth=auth)
            response.raise_for_status()
            data = response.json()
            values = data.get("values", [])
            boards.extend(values)

            if data.get("isLast") is True or len(values) < max_results:
                break
            start_at += max_results

        return boards

    @staticmethod
    def _get_board_sprints(jira_url: str, board_id: int, headers: dict, auth: tuple) -> list:
        endpoint = f"{jira_url}/rest/agile/1.0/board/{board_id}/sprint"
        sprints = []
        start_at = 0
        max_results = 50

        while True:
            params = {
                "startAt": start_at,
                "maxResults": max_results,
                "state": "active,future,closed"
            }
            response = requests.get(endpoint, params=params, headers=headers, auth=auth)
            response.raise_for_status()
            data = response.json()
            values = data.get("values", [])
            sprints.extend(values)

            if data.get("isLast") is True or len(values) < max_results:
                break
            start_at += max_results

        return sprints

    @staticmethod
    def _get_sprint_issues(jira_url: str, sprint_id: int, headers: dict, auth: tuple) -> Dict[str, list]:
        endpoint = f"{jira_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
        issue_ids = []
        issue_keys = []
        start_at = 0
        max_results = 50

        while True:
            params = {
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "id,key"
            }
            response = requests.get(endpoint, params=params, headers=headers, auth=auth)
            response.raise_for_status()
            data = response.json()
            issues = data.get("issues", [])
            for issue in issues:
                issue_id = issue.get("id")
                issue_key = issue.get("key")
                if issue_id:
                    issue_ids.append(issue_id)
                if issue_key:
                    issue_keys.append(issue_key)

            total = data.get("total")
            start_at += len(issues)
            if total is None or start_at >= total:
                break

        return {"issue_ids": issue_ids, "issue_keys": issue_keys}

    def _run(self, project_key: str) -> Dict[str, Dict[str, Any]]:
        """
        Retrieves every sprint for the project's boards and gathers metadata plus assigned issue IDs.

        Args:
            project_key: The Jira project key (e.g., 'PROJ')

        Returns:
            dict: Dictionary keyed by sprint name containing sprint_id, start/end dates, state,
                  board metadata, and issue IDs/keys.
        """
        jira_url = JIRA_URL.rstrip('/')
        auth = (EMAIL, API_KEY)
        headers = {
            "Accept": "application/json"
        }

        boards = self._get_boards(jira_url, project_key, headers, auth)
        if not boards:
            raise ValueError(f"No boards found for project '{project_key}'.")

        all_sprints: Dict[str, Dict[str, Any]] = {}

        for board in boards:
            board_id = board.get("id")
            if board_id is None:
                continue
            board_name = board.get("name", "")
            sprints = self._get_board_sprints(jira_url, board_id, headers, auth)

            for sprint in sprints:
                sprint_id = sprint.get("id")
                sprint_name = sprint.get("name") or f"Sprint {sprint_id or ''}".strip()
                unique_name = sprint_name or f"Sprint {board_id}"
                if unique_name in all_sprints:
                    unique_name = f"{sprint_name} (board {board_id})"
                if unique_name in all_sprints and sprint_id:
                    unique_name = f"{sprint_name} (sprint {sprint_id})"

                issues = self._get_sprint_issues(jira_url, sprint_id, headers, auth) if sprint_id else {"issue_ids": [], "issue_keys": []}

                all_sprints[unique_name] = {
                    "sprint_id": sprint_id,
                    "state": sprint.get("state"),
                    "start_date": self._normalize_date(sprint.get("startDate")),
                    "end_date": self._normalize_date(sprint.get("endDate")),
                    "complete_date": self._normalize_date(sprint.get("completeDate")),
                    "goal": sprint.get("goal"),
                    "board_id": board_id,
                    "board_name": board_name,
                    "issue_ids": issues["issue_ids"],
                    "issue_keys": issues["issue_keys"]
                }

        return all_sprints


class JiraGetSprintIssuesToolInput(BaseModel):
    """Input schema for JiraGetSprintIssuesTool."""
    sprint_id: int = Field(..., description="The numeric ID of the sprint to inspect.")


class JiraGetSprintIssuesTool(BaseTool):
    name: str = "jira_get_sprint_issues"
    description: str = (
        "Returns every issue assigned to a sprint, including issue_id, issue_key, summary, description, type, and status. "
        "Use this after locating a sprint ID via jira_get_all_sprints."
    )
    args_schema: Type[BaseModel] = JiraGetSprintIssuesToolInput

    def _run(self, sprint_id: int) -> Dict[str, Any]:
        """
        Fetches all issues for the specified sprint.

        Args:
            sprint_id: Sprint identifier returned by Jira (integer)

        Returns:
            dict: Contains sprint_id, issue_ids, issue_keys, total count, and a list of issue detail dictionaries.
        """
        if sprint_id is None:
            raise ValueError("sprint_id is required to fetch sprint issues.")

        jira_url = JIRA_URL.rstrip('/')
        auth = (EMAIL, API_KEY)
        headers = {
            "Accept": "application/json"
        }

        endpoint = f"{jira_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
        issue_details = []
        issue_keys = []
        issue_ids = []

        start_at = 0
        max_results = 50

        while True:
            params = {
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "summary,description,issuetype,status"
            }
            response = requests.get(
                endpoint,
                params=params,
                headers=headers,
                auth=auth
            )
            response.raise_for_status()
            data = response.json()
            issues = data.get("issues", [])

            for issue in issues:
                issue_id = issue.get("id")
                issue_key = issue.get("key")
                fields = issue.get("fields", {}) or {}
                description_field = fields.get("description")
                if isinstance(description_field, dict):
                    description = _extract_text_from_adf(description_field)
                elif description_field is None:
                    description = ""
                else:
                    description = str(description_field)

                issue_info = {
                    "issue_id": issue_id,
                    "issue_key": issue_key,
                    "summary": fields.get("summary", ""),
                    "description": description,
                    "issue_type": fields.get("issuetype", {}).get("name", "Unknown"),
                    "status": fields.get("status", {}).get("name", "Unknown")
                }

                issue_details.append(issue_info)
                if issue_id:
                    issue_ids.append(issue_id)
                if issue_key:
                    issue_keys.append(issue_key)

            total = data.get("total")
            retrieved = len(issues)
            start_at += retrieved

            if total is not None and start_at >= total:
                break
            if retrieved == 0:
                break

        return {
            "sprint_id": sprint_id,
            "issues_count": len(issue_details),
            "issue_ids": issue_ids,
            "issue_keys": issue_keys,
            "issues": issue_details
        }


# Tool: JiraUpdateIssueTool
class JiraUpdateIssueToolInput(BaseModel):
    """Input schema for JiraUpdateIssueTool."""
    issue_key: str = Field(..., description="The Jira issue key as a string (e.g., 'MH-9')")
    summary: str = Field("", description="New issue title as a string (e.g., 'Refactor authentication module'). Optional.")
    description: str = Field("", description="New issue description as plain text (e.g., 'Updated requirements...'). Optional.")
    assignee: str = Field("", description="New assignee account ID as a string (e.g., '5fcfd938e40b82006e36206f') not display name or empty string '' to unassign. Optional.")
    priority: str = Field("", description="New priority name as a string: 'Highest', 'High', 'Medium', 'Low', 'Lowest'. Optional.")
    due_date: str = Field("", description="New due date as string in YYYY-MM-DD format (e.g., '2025-12-10'). Optional.")
    start_date: str = Field("", description="New start date as string in YYYY-MM-DD format (e.g., '2025-12-01'). Optional.")
    story_points: int = Field(None, description="New story points as an integer (e.g., 3, 5, 8). Optional.")
    labels: list = Field(None, description="New labels as list of strings (e.g., ['backend', 'urgent']). Replaces existing labels. Optional.")
    status: str = Field("", description="New status name as a string (e.g., 'In Progress', 'Done', 'TODO'). Transitions issue to this status. Optional.")


class JiraUpdateIssueTool(BaseTool):
    name: str = "jira_update_issue"
    description: str = (
        "Updates an existing issue with selective field changes. Provide only fields to update; others remain "
        "unchanged. Handles status transitions automatically. Use assignee='' to unassign. Returns success flag "
        "and list of updated_fields. Essential for adjusting assignments, dates, or priorities after planning."
    )
    args_schema: Type[BaseModel] = JiraUpdateIssueToolInput

    def _run(
        self,
        issue_key: str,
        summary: str = None,
        description: str = None,
        assignee: str = None,
        priority: str = None,
        due_date: str = None,
        start_date: str = None,
        story_points: int = None,
        labels: list = None,
        status: str = None
    ) -> Dict[str, Any]:
        """
        Updates an existing Jira issue with the provided fields.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123')
            summary: New issue summary/title
            description: New issue description (plain text)
            assignee: New assignee account ID (empty string to unassign)
            priority: New priority name (e.g., 'High', 'Medium', 'Low')
            due_date: New due date in format 'YYYY-MM-DD'
            start_date: New start date in format 'YYYY-MM-DD'
            story_points: New story points value
            labels: New list of labels (replaces existing labels)
            status: New status name (e.g., 'In Progress', 'Done')
        
        Returns:
            dict: Dictionary containing:
                - success: True if successful
                - updated_fields: List of fields that were updated
                - issue_key: The updated issue key
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        jira_url = JIRA_URL.rstrip('/')
        auth = (EMAIL, API_KEY)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Build the fields to update
        fields = {}
        updated_fields = []
        
        if summary is not None:
            fields["summary"] = summary
            updated_fields.append("summary")
        
        if description is not None:
            # Convert to ADF format
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            }
            updated_fields.append("description")
        
        if assignee is not None:
            # If assignee is empty string, unassign
            if assignee == "":
                fields["assignee"] = None
            else:
                fields["assignee"] = {"accountId": assignee}
            updated_fields.append("assignee")
        
        if priority is not None:
            fields["priority"] = {"name": priority}
            updated_fields.append("priority")
        
        if due_date is not None:
            fields["duedate"] = due_date
            updated_fields.append("due_date")
        
        if start_date is not None:
            fields["customfield_10015"] = start_date  # Common start date field
            updated_fields.append("start_date")
        
        if story_points is not None:
            fields["customfield_10016"] = story_points  # Common story points field
            updated_fields.append("story_points")
        
        if labels is not None:
            fields["labels"] = labels if isinstance(labels, list) else [labels]
            updated_fields.append("labels")
        
        # Update the issue fields
        if fields:
            endpoint = f"{jira_url}/rest/api/3/issue/{issue_key}"
            response = requests.put(
                endpoint,
                json={"fields": fields},
                headers=headers,
                auth=auth
            )
            
            if response.status_code != 204:  # 204 is success for PUT
                response.raise_for_status()
        
        # Handle status transition separately (if provided)
        if status is not None:
            # Get available transitions
            transitions_url = f"{jira_url}/rest/api/3/issue/{issue_key}/transitions"
            transitions_response = requests.get(
                transitions_url,
                headers=headers,
                auth=auth
            )
            transitions_response.raise_for_status()
            transitions_data = transitions_response.json()
            
            # Find the transition ID for the target status
            transition_id = None
            for transition in transitions_data.get('transitions', []):
                if transition.get('to', {}).get('name', '').lower() == status.lower():
                    transition_id = transition.get('id')
                    break
            
            if transition_id:
                # Execute the transition
                transition_response = requests.post(
                    transitions_url,
                    json={"transition": {"id": transition_id}},
                    headers=headers,
                    auth=auth
                )
                transition_response.raise_for_status()
                updated_fields.append("status")
            else:
                # Status transition not found
                available_statuses = [t.get('to', {}).get('name') for t in transitions_data.get('transitions', [])]
                return {
                    "success": False,
                    "error": f"Could not find transition to status '{status}'",
                    "available_transitions": available_statuses,
                    "issue_key": issue_key
                }
        
        return {
            "success": True,
            "updated_fields": updated_fields,
            "issue_key": issue_key
        }
