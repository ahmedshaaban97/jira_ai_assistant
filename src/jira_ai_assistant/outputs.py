"""
Pydantic output models for CrewAI tasks.
These models define the structured output expected from each task.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Plan Epic Backlog Output Models
# ============================================================================

class RiskItem(BaseModel):
    """Risk item model for epic planning."""
    id: str = Field(..., description="Unique risk identifier")
    description: str = Field(..., description="Description of the risk")
    impact: str = Field(..., description="Impact assessment (e.g., 'High', 'Medium', 'Low')")
    mitigation: str = Field(..., description="Proposed mitigation strategy")


class BacklogItem(BaseModel):
    """Individual backlog item model."""
    title: str = Field(..., description="Concise issue title")
    type: str = Field(..., description="One of: 'Story', 'Task', 'Bug', 'Sub-task'")
    parent_hint: Optional[str] = Field(None, description="Epic key or parent issue key/name if it should be a Sub-task")
    description: str = Field(..., description="Clear plain-text description, including acceptance criteria")
    labels: Optional[List[str]] = Field(None, description="List of suggested labels")
    components: Optional[List[str]] = Field(None, description="List of suggested components")
    story_points_hint: Optional[int] = Field(None, description="Suggested story points value")
    assignee: Optional[str] = Field(
        None,
        description="Best candidate assignee accountId for this item (not display name)",
    )
    dependency_hints: Optional[List[str]] = Field(None, description="List of titles/keys that should precede this item")
    schedule_hint: Optional[str] = Field(None, description="Suggested start/due date ranges relative to epic timeline")
    sub_tasks_hint: Optional[List[str]] = Field(
        None,
        description=(
            "For Story items, list of suggested Sub-task titles covering development, "
            "testing, documentation, and deployment/release work"
        ),
    )
    sprint_hint: Optional[str] = Field(
        None,
        description=(
            "Suggested sprint name or identifier this item should eventually be assigned to; "
            "should not be empty for in-scope work items"
        ),
    )


class PlanEpicBacklogOutput(BaseModel):
    """Output model for plan_epic_backlog task."""
    epic_summary: str = Field(..., description="Short plain-text summary of the epic")
    assumptions: List[str] = Field(default_factory=list, description="List of assumptions about scope, timelines, and capacity")
    risks: List[RiskItem] = Field(default_factory=list, description="List of risk items")
    backlog_items: List[BacklogItem] = Field(default_factory=list, description="Array of backlog items to be created")
    schedule_overview: str = Field(..., description="Plain-text explanation of how work should be sequenced")


# ============================================================================
# Execute Epic Backlog Output Models
# ============================================================================

class CreatedIssue(BaseModel):
    """Model for a created Jira issue."""
    issue_key: str = Field(..., description="Jira issue key (e.g., 'MH-123')")
    issue_type: str = Field(..., description="Type: 'Story', 'Task', 'Bug', 'Sub-task'")
    summary: str = Field(..., description="Final issue summary/title")
    description_summary: Optional[str] = Field(
        None,
        description=(
            "Brief summary of what was included in the full Jira description "
            "(e.g., acceptance criteria count, DoD highlights, testing scope)"
        ),
    )
    assignee: Optional[str] = Field(
        None,
        description="AccountId of assignee (preferred) or display name if accountId is unavailable",
    )
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format or null")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format or null")
    story_points: Optional[int] = Field(None, description="Story points value or null")
    parent_key: Optional[str] = Field(None, description="Parent issue key for sub-tasks, else null")
    sub_tasks_created: Optional[List[str]] = Field(
        None,
        description="For Story issues, list of Sub-task keys created under this Story",
    )
    sprint_id: Optional[int] = Field(
        None,
        description="Numeric sprint identifier that this issue was moved into",
    )
    sprint_name: Optional[str] = Field(
        None,
        description="Human-readable sprint name that this issue belongs to",
    )


class UpdatedIssue(BaseModel):
    """Model for an updated Jira issue."""
    issue_key: str = Field(..., description="Jira issue key (e.g., 'MH-123')")
    issue_type: str = Field(..., description="Type: 'Story', 'Task', 'Bug', 'Sub-task'")
    summary: str = Field(..., description="Final issue summary/title")
    assignee: Optional[str] = Field(None, description="Display name or accountId of assignee")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format or null")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format or null")
    story_points: Optional[int] = Field(None, description="Story points value or null")
    parent_key: Optional[str] = Field(None, description="Parent issue key for sub-tasks, else null")
    updated_fields: List[str] = Field(default_factory=list, description="List of fields that were updated")


class CommentAdded(BaseModel):
    """Model for a comment added to a Jira issue."""
    issue_key: str = Field(..., description="Issue key where the comment was added")
    comment_summary: str = Field(..., description="Short description of the comment content (not full text)")


class ExecuteEpicBacklogOutput(BaseModel):
    """Output model for execute_epic_backlog task."""
    epic_key: str = Field(..., description="The epic key being executed")
    created_issues: List[CreatedIssue] = Field(default_factory=list, description="Array of created issues")
    updated_issues: List[UpdatedIssue] = Field(default_factory=list, description="Array of updated issues")
    comments_added: List[CommentAdded] = Field(default_factory=list, description="Array of comments added to issues")
    capacity_notes: str = Field(..., description="Plain-text explanation of capacity and availability considerations")


# ============================================================================
# Follow-up Sprint Tasks Output Models
# ============================================================================

class SprintReviewed(BaseModel):
    """Model for a reviewed sprint."""
    sprint_id: int = Field(..., description="The sprint ID")
    sprint_name: str = Field(..., description="The sprint name")
    sprint_state: str = Field(..., description="The sprint state (should be 'active')")
    task_count: int = Field(..., description="Number of tasks in this sprint")


class TaskFollowedUp(BaseModel):
    """Model for a task that received a follow-up comment."""
    issue_key: str = Field(..., description="The Jira issue key")
    summary: str = Field(..., description="The issue summary/title")
    status: str = Field(..., description="Current issue status")
    assignee: Optional[str] = Field(None, description="Assignee display name or account ID")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format or null")
    days_until_due: Optional[int] = Field(None, description="Days until due (negative if overdue, null if no due date)")
    comment_added: bool = Field(..., description="Whether comment was successfully added")
    comment_summary: Optional[str] = Field(None, description="Brief summary of the comment content (null if comment was not added)")


class FollowUpSprintTasksOutput(BaseModel):
    """Output model for follow_up_sprint_tasks task."""
    project_key: str = Field(..., description="The project key reviewed")
    sprints_reviewed: List[SprintReviewed] = Field(default_factory=list, description="Array of sprints reviewed")
    tasks_followed_up: List[TaskFollowedUp] = Field(default_factory=list, description="Array of tasks that received follow-up comments")
    summary: str = Field(..., description="Overall summary of follow-up actions and observations")

