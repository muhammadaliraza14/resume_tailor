from __future__ import annotations

from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from resume_tailor.models import (
    JobDescriptionStructure,
    ResumeEvaluation,
    StructuredResumeContent,
)
from resume_tailor.tools.resume_tools import (
    AtsResumeMetricsTool,
    GetAtsGuidelinesTool,
    KeywordSimilarityTool,
    ReadTailoredResumeTextTool,
    ReadTextFileTool,
    WriteStructuredResumeTool,
)


@CrewBase
class ResumeTailorCrew:
    """Text-in resume + JD; PDF out matches resume_template.pdf layout."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def resume_parsing_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["resume_parsing_agent"],
            tools=[ReadTextFileTool()],
            verbose=True,
        )

    @agent
    def job_description_parsing_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["job_description_parsing_agent"],
            tools=[ReadTextFileTool()],
            verbose=True,
        )

    @agent
    def tailoring_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["tailoring_agent"],
            tools=[WriteStructuredResumeTool()],
            verbose=True,
        )

    @agent
    def evaluator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["evaluator_agent"],
            tools=[
                ReadTailoredResumeTextTool(),
                ReadTextFileTool(),
                KeywordSimilarityTool(),
                AtsResumeMetricsTool(),
                GetAtsGuidelinesTool(),
            ],
            verbose=True,
        )

    @task
    def parse_resume_task(self) -> Task:
        return Task(
            config=self.tasks_config["parse_resume_task"],
            output_pydantic=StructuredResumeContent,
            async_execution=True,
        )

    @task
    def parse_job_description_task(self) -> Task:
        return Task(
            config=self.tasks_config["parse_job_description_task"],
            output_pydantic=JobDescriptionStructure,
            async_execution=True,
        )

    @task
    def tailor_resume_task(self) -> Task:
        return Task(
            config=self.tasks_config["tailor_resume_task"],
        )

    @task
    def evaluate_resume_task(self) -> Task:
        return Task(
            config=self.tasks_config["evaluate_resume_task"],
            output_pydantic=ResumeEvaluation,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
