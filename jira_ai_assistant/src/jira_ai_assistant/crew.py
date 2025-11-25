from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class JiraAiAssistant():
    """JiraAiAssistant crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def product_manger(self) -> Agent:
        return Agent(
            config=self.agents_config['product_manger'], # type: ignore[index]
            verbose=True,
            
        )

    @task
    def create_epic_issues(self) -> Task:
        return Task(
            config=self.tasks_config['create_epic_issues'], # type: ignore[index]
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
