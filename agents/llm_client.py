import warnings
warnings.filterwarnings("ignore")  # suppress CrewAI's internal Pydantic serialization warnings

import litellm
litellm.drop_params = True
litellm.suppress_debug_info = True  # suppress "response: <Response [200 OK]>" logging

import crewai.llms.cache as _crewai_cache
_crewai_cache.mark_cache_breakpoint = lambda msg: msg

from crewai import Agent, Task, Crew, Process, LLM
from config import GROQ_API_KEY, GROQ_MODEL

_llm = LLM(model=f"groq/{GROQ_MODEL}", api_key=GROQ_API_KEY)


def complete(system: str, user: str, max_tokens: int = 800, temperature: float = 0.7) -> str:
    """Single-turn completion helper shared by all agents.
    Internally, every LLM call is executed as a one-agent, one-task CrewAI
    Crew, so drafting, revising, and reviewing all run through CrewAI's
    Agent/Task/Crew orchestration rather than a raw API call."""
    agent = Agent(
        role="AI Email Assistant",
        goal="Follow the given instructions precisely and produce exactly the requested output.",
        backstory=system,
        llm=LLM(model=f"groq/{GROQ_MODEL}", api_key=GROQ_API_KEY, temperature=temperature),
        verbose=False,
    )

    task = Task(
        description=user,
        expected_output="The exact output requested in the instructions, in the required format.",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()
    return str(result).strip()