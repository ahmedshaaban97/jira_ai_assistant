from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from .tools.files_retrieval_tools import PdfFileRetriever
from .tools.jira_tools import JiraCreateIssueTool, JiraUpdateIssueTool, JiraAssignIssueTool, JiraAddCommentTool, JiraGetAllIssuesWithDetailsTool, JiraGetUserHistoryTool, JiraGetAllEpicsTool, JiraGetAllUsersTool, JiraGetIssueDetailsTool
from .outputs import PlanEpicBacklogOutput, ExecuteEpicBacklogOutput



@CrewBase
class JiraAiAssistant():
    """JiraAiAssistant crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def product_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['product_manager'], # type: ignore[index]
            verbose=True,
            tools=[PdfFileRetriever(), JiraCreateIssueTool(), JiraUpdateIssueTool(), JiraAssignIssueTool(), JiraAddCommentTool(), JiraGetAllIssuesWithDetailsTool(), JiraGetUserHistoryTool(), JiraGetAllEpicsTool(), JiraGetAllUsersTool(), JiraGetIssueDetailsTool()]
        )

    @task
    def plan_epic_backlog(self) -> Task:
        return Task(
            config=self.tasks_config['plan_epic_backlog'], # type: ignore[index]
            output_pydantic=PlanEpicBacklogOutput,
        )

    @task
    def execute_epic_backlog(self) -> Task:
        return Task(
            config=self.tasks_config['execute_epic_backlog'], # type: ignore[index]
            output_pydantic=ExecuteEpicBacklogOutput,
        )


    @crew
    def crew(self) -> Crew:
        """Creates the JiraAiAssistant crew"""
        

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
