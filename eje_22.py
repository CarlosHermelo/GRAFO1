import os
import warnings
import logging

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from neo4j_for_adk import tool_success, tool_error

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.CRITICAL)

print("Libraries imported.")

# ========================
# MODELO
# ========================
llm = LiteLlm(model="openai/gpt-4o")

print(
    llm.llm_client.completion(
        model=llm.model,
        messages=[{"role": "user", "content": "Are you ready?"}],
        tools=[]
    )
)
print("OpenAI is ready.\n")

# ============================
# DEFINICIÓN DE TOOLS
# ============================
PERCEIVED_USER_GOAL = "perceived_user_goal"
APPROVED_USER_GOAL = "approved_user_goal"

def set_perceived_user_goal(kind_of_graph: str, graph_description: str, tool_context: ToolContext):
    data = {
        "kind_of_graph": kind_of_graph,
        "graph_description": graph_description
    }
    tool_context.state[PERCEIVED_USER_GOAL] = data
    return tool_success(PERCEIVED_USER_GOAL, data)

def approve_perceived_user_goal(tool_context: ToolContext):
    if PERCEIVED_USER_GOAL not in tool_context.state:
        return tool_error("No perceived user goal found.")
    approved = tool_context.state[PERCEIVED_USER_GOAL]
    tool_context.state[APPROVED_USER_GOAL] = approved
    return tool_success(APPROVED_USER_GOAL, approved)

# ============================
# INSTRUCCIONES DEL AGENTE
# ============================
instruction = """
You are an expert at knowledge graph use cases.
Your goal is to help the user define a knowledge graph use case.

Ask questions, understand what graph they want,
use the tool 'set_perceived_user_goal',
then ask for confirmation, and finally
use 'approve_perceived_user_goal'.
"""

# ========================
# CREACIÓN DEL AGENTE
# ========================
user_intent_agent = Agent(
    name="user_intent_agent",
    instruction=instruction,
    model=llm,
    tools=[set_perceived_user_goal, approve_perceived_user_goal]
)

# ========================
# RUNNER
# ========================
session_service = InMemorySessionService()

runner = Runner(
    app_name="intent_app",
    agent=user_intent_agent,
    session_service=session_service
)

# ========================
# EJECUCIÓN REAL
# ========================
print("=== OUTPUT DEL AGENTE ===\n")

events = runner.run(
    user_id="carlos",
    session_id="s1",
    new_message=types.Content(
        role="user",
        parts=[types.TextPart(text="Hola, quiero hacer un grafo pero no sé bien de qué.")]
    )
)

for event in events:
    print(event)
