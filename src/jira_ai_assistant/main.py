#!/usr/bin/env python
import sys
import warnings

from datetime import datetime
from crewai import Crew, Process

from jira_ai_assistant.crew import JiraAiAssistant

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information
from dotenv import load_dotenv
load_dotenv()


def route_workflow(user_msg, epic_key=""):
    """
    Analyze user message to determine which workflow to run.
    Returns: "follow_up" or "backlog"
    """
    user_msg_lower = user_msg.lower()
    
    # Follow-up indicators
    follow_up_keywords = [
        "follow up", "follow-up", "check on", "check in",
        "status update", "progress update", "what's the status",
        "active tasks", "current tasks", "sprint tasks",
        "sprint review", "sprint check", "review sprint",
        "task status", "how are tasks", "task progress",
        "overdue", "delayed", "behind schedule"
    ]
    
    # Backlog indicators
    backlog_keywords = [
        "epic", "backlog", "breakdown", "plan", "plan-epic",
        "create issues", "decompose", "generate tasks",
        "create stories", "build backlog", "sprint planning",
        "capacity planning", "new feature", "requirement"
    ]
    
    # Count matches
    follow_up_score = sum(1 for keyword in follow_up_keywords if keyword in user_msg_lower)
    backlog_score = sum(1 for keyword in backlog_keywords if keyword in user_msg_lower)
    
    # Make decision
    if follow_up_score > backlog_score:
        return "follow_up"
    elif backlog_score > 0 or epic_key:
        return "backlog"
    else:
        # Default to follow-up if no clear indicators
        return "follow_up"


def run(inputs={}):
    """
    Run the crew with routing logic based on user_msg.
    """
    # print(f"Inputs: {inputs}")
    # return
    # Example inputs - modify these as needed
    # inputs = {
    #     'project_key': 'MH',
    #     'epic_key': 'MH-6',
    #     'user_msg': 'backlog',  # User's natural language message
    # }
    if not inputs:
        print("No inputs provided")
        return
    else:
        print(f"Inputs: {inputs}")

    try:
        crew_instance = JiraAiAssistant()
        
        # Check if user_msg is provided for routing
        if 'user_msg' in inputs and inputs['user_msg']:
            # Route based on user message
            print(f"\n{'='*60}")
            print("ANALYZING USER MESSAGE")
            print(f"{'='*60}")
            print(f"Message: {inputs['user_msg']}")
            
            workflow_type = route_workflow(inputs['user_msg'], inputs.get('epic_key', ''))
            
            print(f"Decision: {workflow_type.upper()} workflow")
            print(f"{'='*60}\n")
            
            # Execute the appropriate workflow
            if workflow_type == "follow_up":
                # Run follow-up workflow
                print(f"\n{'='*60}")
                print("EXECUTING FOLLOW-UP WORKFLOW")
                print(f"{'='*60}\n")
                
                follow_up_crew = Crew(
                    agents=[crew_instance.follow_up_agent()],
                    tasks=[crew_instance.follow_up_sprint_tasks()],
                    process=Process.sequential,
                    verbose=True,
                )
                
                result = follow_up_crew.kickoff(inputs=inputs)
                
                print(f"\n{'='*60}")
                print("FOLLOW-UP WORKFLOW COMPLETE")
                print(f"{'='*60}")
                if hasattr(result, 'pydantic') and result.pydantic:
                    print(f"Project: {result.pydantic.project_key}")
                    print(f"Sprints reviewed: {len(result.pydantic.sprints_reviewed)}")
                    print(f"Tasks followed up: {len(result.pydantic.tasks_followed_up)}")
                    print(f"Summary: {result.pydantic.summary}")
                print(f"{'='*60}\n")
                
            else:  # backlog workflow
                # Run backlog workflow
                print(f"\n{'='*60}")
                print("EXECUTING BACKLOG WORKFLOW")
                print(f"{'='*60}\n")
                
                if not inputs.get('epic_key'):
                    raise ValueError("epic_key is required for backlog workflow")
                
                backlog_crew = Crew(
                    agents=[crew_instance.product_manager()],
                    tasks=[
                        crew_instance.plan_epic_backlog(),
                        crew_instance.execute_epic_backlog(),
                    ],
                    process=Process.sequential,
                    verbose=True,
                )
                
                result = backlog_crew.kickoff(inputs=inputs)
                
                print(f"\n{'='*60}")
                print("BACKLOG WORKFLOW COMPLETE")
                print(f"{'='*60}\n")
        else:
            # No user_msg provided, run the original backlog workflow directly
            print(f"\n{'='*60}")
            print("RUNNING DEFAULT BACKLOG WORKFLOW (No routing)")
            print(f"{'='*60}\n")
            
            result = crew_instance.crew().kickoff(inputs=inputs)
        return result
            
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
