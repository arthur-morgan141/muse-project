"""
Local agent tools and tool registration matching Meta Muse Mobile MCP interface.
"""

from typing import Any, Callable, Dict, List


class MuseToolRegistry:
    """Registry for MCP tools exposed to or consumed by Meta Muse."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        schema: Dict[str, Any],
        handler: Callable[..., Any],
    ) -> None:
        self._tools[name] = {
            "name": name,
            "description": description,
            "input_schema": schema,
            "handler": handler,
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": v["name"],
                "description": v["description"],
                "input_schema": v["input_schema"],
            }
            for v in self._tools.values()
        ]

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' is not registered.")
        return self._tools[name]["handler"](**arguments)
