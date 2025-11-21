# ========================
# BLOQUE 1 — SETUP INICIAL
# ========================

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

from neo4j_for_adk import graphdb, tool_success, tool_error

import warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.CRITICAL)

print("Libraries imported.")

# Modelo
MODEL_GPT = "openai/gpt-4o"
llm = LiteLlm(model=MODEL_GPT)

# Test simple
print(
    llm.llm_client.completion(
        model=llm.model,
        messages=[{"role": "user", "content": "Are you ready?"}],
        tools=[]
    )
)
print("\nOpenAI is ready.")


# ============================
# BLOQUE 2 — DEFINICIÓN TOOLS
# ============================

PERCEIVED_USER_GOAL = "perceived_user_goal"
APPROVED_USER_GOAL = "approved_user_goal"

def set_perceived_user_goal(kind_of_graph: str, graph_description: str, tool_context: ToolContext):
    """Guarda la interpretación preliminar del agente sobre el objetivo del usuario."""
    data = {
        "kind_of_graph": kind_of_graph,
        "graph_description": graph_description
    }
    tool_context.state[PERCEIVED_USER_GOAL] = data
    return tool_success(PERCEIVED_USER_GOAL, data)

def approve_perceived_user_goal(tool_context: ToolContext):
    """Aprueba el objetivo percibido y lo pasa al estado como objetivo final."""
    if PERCEIVED_USER_GOAL not in tool_context.state:
        return tool_error("No perceived user goal found to approve.")
    approved = tool_context.state[PERCEIVED_USER_GOAL]
    tool_context.state[APPROVED_USER_GOAL] = approved
    return tool_success(APPROVED_USER_GOAL, approved)

# ======================================
# BLOQUE 3 — INSTRUCCIONES DEL AGENTE
# ======================================

agent_role_and_goal = """
You are an expert at knowledge graph use cases.
Your goal is to help the user define a knowledge graph use case.
"""

agent_conversational_hints = """
If the user is unsure, suggest classic graph use cases such as:
- social network
- logistics network
- recommendation system
- fraud detection
- pop-culture graphs
"""

agent_output_definition = """
A user goal has two fields:
- kind_of_graph: at most 3 words
- description: a paragraph describing the purpose
"""

agent_chain_of_thought_directions = """
Follow these steps:
1. Understand the user's goal
2. Ask questions if needed
3. Use 'set_perceived_user_goal' to record your interpretation
4. Present it to the user
5. If user agrees, call 'approve_perceived_user_goal'
"""

complete_agent_instruction = f"""
{agent_role_and_goal}
{agent_conversational_hints}
{agent_output_definition}
{agent_chain_of_thought_directions}
"""


# ===============================
# BLOQUE 4 — CREACIÓN DEL AGENTE
# ===============================

user_intent_agent = Agent(
    name="user_intent_agent",
    instruction=complete_agent_instruction,
    model=llm,
    tools=[set_perceived_user_goal, approve_perceived_user_goal]
)


# =======================================
# BLOQUE 5 — RUNNER (EJEMPLO DE EJECUCIÓN)
# =======================================

session_service = InMemorySessionService()

runner = Runner(
    app_name="user_intent_app",
    agent=user_intent_agent,
    session_service=session_service
)

# Ejemplo de inicio (interacción real):
# runner.run() devuelve un generador, necesitamos iterar sobre él
# new_message debe ser un objeto Content (tipos de google.genai)
from google.genai.types import Content, Part

# Crear una sesión primero
user_id = "user_1"
session_id = "session_1"
app_name = "user_intent_app"

# Crear la sesión en el servicio de sesiones
session = session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

message = Content(role="user", parts=[Part(text="Hola, quiero hacer un grafo pero no sé bien de qué.")])

for response in runner.run(
    user_id=user_id,
    session_id=session_id,
    new_message=message
):
    print(response)
