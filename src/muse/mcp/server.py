"""
MCP Server runtime scaffolding for Meta Muse agentic tools.
"""

from typing import Optional

from muse.core.config import MuseConfig, get_config
from muse.core.logging import setup_logger
from muse.mcp.tools import MuseToolRegistry

logger = setup_logger("muse.mcp")


class MuseMcpServer:
    """Scaffolding for local MCP server integration."""

    def __init__(self, config: Optional[MuseConfig] = None):
        self.config = config or get_config()
        self.registry = MuseToolRegistry()

    def start(self) -> None:
        logger.info(
            f"Starting Muse MCP Server stub on {self.config._data.get('mcp', {}).get('host', '127.0.0.1')}:"
            f"{self.config._data.get('mcp', {}).get('port', 8765)}"
        )
