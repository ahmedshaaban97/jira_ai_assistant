import os
from typing import Any, Dict, Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, field_validator

from .utils import _extract_text_from_adf, _format_date, load_jira_env

# Load environment variables
load_jira_env()

JIRA_URL = os.getenv("JIRA_URL", "")
EMAIL = os.getenv("EMAIL", "")
API_KEY = os.getenv("API_KEY", "")


# Tool: JiraAddCommentTool
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


# Tool: JiraAssignIssueTool
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


# Tool: JiraGetAllUsersTool
class JiraGetAllUsersToolInput(BaseModel):
    """Input schema for JiraGetAllUsersTool."""
    project_key: str = Field(..., description="The Jira project key (e.g., 'MH', 'PROJ')")


class JiraGetAllUsersTool(BaseTool):
    name: str = "jira_get_all_users"
    description: str = (
        "Gets all users in a project. Returns a list of dictionaries where each dictionary maps an accountId to the "
        "user's display name."
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


# Tool: JiraGetAllEpicsTool
class JiraGetAllEpicsToolInput(BaseModel):
    """Input schema for JiraGetAllEpicsTool."""
    project_key: str = Field(..., description="The Jira project key (e.g., 'MH', 'PROJ')")


class JiraGetAllEpicsTool(BaseTool):
    name: str = "jira_get_all_epics"
    description: str = (
        "Gets all epics for a given project. Returns a list of epics with their summary, key, description, "
        "creation date, start date, due date, and status."
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
    issue_key: str = Field(..., description="The Jira issue key or ID (e.g., 'PROJ-123' or '10038')")


class JiraGetIssueDetailsTool(BaseTool):
    name: str = "jira_get_issue_details"
    description: str = (
        "Gets detailed information for a specific Jira issue. Returns comprehensive details including "
        "summary, description, status, dates, assignee, priority, epic link, parent, story points, labels, and components."
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
    project_key: str = Field(..., description="The Jira project key (e.g., 'PROJ')")
    epic_key: str = Field("", description="Optional epic key to filter issues (e.g., 'PROJ-7'). If None, returns all issues in the project.")


class JiraGetAllIssuesWithDetailsTool(BaseTool):
    name: str = "jira_get_all_issues_with_details"
    description: str = (
        "Gets all issues for a given project, optionally filtered by epic. Returns full details for each issue. "
        "Use this when you need comprehensive information about all issues in a project or epic."
    )
    args_schema: Type[BaseModel] = JiraGetAllIssuesWithDetailsToolInput

    def _run(self, project_key: str, epic_key: str = "") -> list:
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


# Define regex for Account id (hex string, variable length); pydantic-core uses Rust regex (no lookaheads)
# ACCOUNT_ID_PATTERN = r'^[0-9a-fA-F]+$'
# AccountId = constr(pattern=ACCOUNT_ID_PATTERN)

# Tool: JiraCreateIssueTool
class JiraCreateIssueToolInput(BaseModel):
    """Input schema for JiraCreateIssueTool."""
    project_key: str = Field(..., description="The project key (e.g., 'PROJ')")
    summary: str = Field(..., description="The issue summary/title")
    description: str = Field(..., description="The issue description (plain text)")
    issue_type: str = Field(default="Task", description="The type of issue (e.g., 'Task', 'Story', 'Bug', 'Sub-task')")
    epic_key: str = Field("", description="The epic key to link the issue to (e.g., 'PROJ-7'). Ignored for sub-tasks.")
    parent_key: str = Field("", description="The parent issue key for sub-tasks (e.g., 'PROJ-10')")
    start_date: str = Field("", description="Start date in format 'YYYY-MM-DD'")
    due_date: str = Field("", description="Due date in format 'YYYY-MM-DD'")
    assignee: str = Field(
        pattern=r'^[0-9a-fA-F]+$',
        description=(
            "Assignee account ID, cannot be the assignee name! "
            "IT MUST BE ASSIGNEE ID like: 5fcfd938e40b82006e36206f"
        ),
    )
    story_points: int = Field(None, description="Story points value")

    @field_validator("assignee")
    @classmethod
    def validate_assignee(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Assignee ID must contain at least one digit (0–9).")
        if not any(c.isalpha() for c in v):
            raise ValueError("Assignee ID must contain at least one letter (a–f or A–F).")
        return v

class JiraCreateIssueTool(BaseTool):
    name: str = "jira_create_issue"
    description: str = (
        "Creates a new Jira issue (Task, Story, Bug, or Sub-task). Can link to an epic and set dates, assignee, "
        "and story points. For sub-tasks, provide parent_key and the epic will be inherited from the parent."
    )
    args_schema: Type[BaseModel] = JiraCreateIssueToolInput

    def _run(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        epic_key: str = "",
        parent_key: str = "",
        start_date: str = "",
        due_date: str = "",
        assignee: str = "",
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


# Tool: JiraUpdateIssueTool
class JiraUpdateIssueToolInput(BaseModel):
    """Input schema for JiraUpdateIssueTool."""
    issue_key: str = Field(..., description="The Jira issue key (e.g., 'PROJ-123')")
    summary: str = Field("", description="New issue summary/title")
    description: str = Field("", description="New issue description (plain text)")
    assignee: str = Field("", description="New assignee account ID (empty string to unassign)")
    priority: str = Field("", description="New priority name (e.g., 'High', 'Medium', 'Low')")
    due_date: str = Field("", description="New due date in format 'YYYY-MM-DD'")
    start_date: str = Field("", description="New start date in format 'YYYY-MM-DD'")
    story_points: int = Field(None, description="New story points value")
    labels: list = Field(None, description="New list of labels (replaces existing labels)")
    status: str = Field("", description="New status name (e.g., 'In Progress', 'Done')")


class JiraUpdateIssueTool(BaseTool):
    name: str = "jira_update_issue"
    description: str = (
        "Updates an existing Jira issue with the provided fields. Can update summary, description, assignee, "
        "priority, dates, story points, labels, and status. Only updates the fields you provide. "
        "Status changes are handled via transitions."
    )
    args_schema: Type[BaseModel] = JiraUpdateIssueToolInput

    def _run(
        self,
        issue_key: str,
        summary: str = "",
        description: str = "",
        assignee: str = "",
        priority: str = "",
        due_date: str = "",
        start_date: str = "",
        story_points: int = None,
        labels: list = None,
        status: str = ""
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
