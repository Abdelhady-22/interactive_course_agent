"""Crew factory — creates CrewAI Crew objects with agents and tasks."""

from __future__ import annotations

from crewai import Agent, Task, Crew, Process, LLM

from app.config import Settings
from app.agents.prompts import DIRECTOR_SYSTEM_PROMPT, REVIEW_SYSTEM_PROMPT
from app.utils.logger import logger


def create_llm(settings: Settings) -> LLM:
    """Create a CrewAI-compatible LLM from settings."""
    provider = settings.llm_provider.lower()

    if provider == "ollama":
        model_string = f"ollama/{settings.llm_model}"
    elif provider == "groq":
        model_string = f"groq/{settings.llm_model}"
    elif provider == "openai":
        model_string = settings.llm_model
    elif provider == "anthropic":
        model_string = f"anthropic/{settings.llm_model}"
    elif provider == "cohere":
        model_string = f"cohere/{settings.llm_model}"
    else:
        model_string = f"{provider}/{settings.llm_model}"

    return LLM(
        model=model_string,
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout,
    )


def create_director_agent(settings: Settings) -> Agent:
    """Create the Layout Director CrewAI Agent."""
    llm = create_llm(settings)

    return Agent(
        role="Expert Educational Video Layout Director",
        goal="Decide the best screen layout for each paragraph to maximize learning impact.",
        backstory=(
            "You are a world-class educational video director with 15 years of experience. "
            "You understand how screen composition, visual hierarchy, and pacing affect learning. "
            "Every layout choice you make serves the teaching moment."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def create_reviewer_agent(settings: Settings) -> Agent:
    """Create the Layout Quality Reviewer CrewAI Agent."""
    llm = create_llm(settings)

    return Agent(
        role="Layout Quality Reviewer",
        goal="Review rule-engine layout decisions and approve or improve them.",
        backstory=(
            "You are a quality-assurance specialist for educational video layouts. "
            "You evaluate automated decisions against best practices and learner experience. "
            "Be concise — only override when the rule clearly made a suboptimal choice."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def create_layout_task(agent: Agent, user_prompt: str) -> Task:
    """Create a layout decision task."""
    return Task(
        description=user_prompt,
        expected_output="A JSON object with the layout decision for the paragraph.",
        agent=agent,
    )


def create_review_task(agent: Agent, user_prompt: str) -> Task:
    """Create a review task."""
    return Task(
        description=user_prompt,
        expected_output='A JSON object with "approved": true or "approved": false and an "override" object.',
        agent=agent,
    )


def create_crew(agents: list[Agent], tasks: list[Task]) -> Crew:
    """Create a CrewAI Crew with sequential processing."""
    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=False,
    )
