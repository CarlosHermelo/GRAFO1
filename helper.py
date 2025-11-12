from typing import Any


class AgentCaller:
	def __init__(self, agent: Any, tool_context: Any):
		self._agent = agent
		self._tool_context = tool_context

	async def call(self, input_text: str) -> Any:
		# Intentamos métodos comunes de agentes async
		if hasattr(self._agent, "call"):
			return await self._agent.call(input_text, tool_context=self._tool_context)
		if hasattr(self._agent, "run"):
			return await self._agent.run(input_text, tool_context=self._tool_context)
		# Fallback: si fuese sync
		if hasattr(self._agent, "invoke"):
			return self._agent.invoke(input_text, tool_context=self._tool_context)
		raise AttributeError("El agente no expone 'call', 'run' ni 'invoke'.")


def make_agent_caller(agent: Any, tool_context: Any) -> AgentCaller:
	"""
	Devuelve un pequeño wrapper con método async 'call(input_text)' que
	inyecta el 'tool_context' al agente subyacente.
	"""
	return AgentCaller(agent, tool_context)
