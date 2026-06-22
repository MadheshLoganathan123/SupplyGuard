"""
BaseAgent — abstract foundation for all SupplyGuard AI agents.
Each agent can perceive state, decide an action, and execute it.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class AgentContext:
    """Shared context passed to every agent decision cycle."""
    sector: str
    threat_level: str
    active_incidents: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Optional computed attributes (set by ProfileContextService)
    inventory_status: Optional[str] = None  # "LOW", "NORMAL", "HIGH"
    sector_demand_level: Optional[str] = None  # "LOW", "NORMAL", "HIGH"


@dataclass
class AgentAction:
    """Result returned by an agent after deciding on an action."""
    agent_name: str
    action_type: str
    payload: Dict[str, Any]
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BaseAgent(ABC):
    """
    Abstract base class for all supply-chain agents.

    Subclasses must implement:
        - perceive()  → gather relevant state
        - decide()    → choose an action given perceived state
        - act()       → execute the chosen action
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def perceive(self, context: AgentContext) -> Dict[str, Any]:
        """Gather relevant information from the environment."""

    @abstractmethod
    async def decide(self, perception: Dict[str, Any]) -> AgentAction:
        """Choose the best action based on perceived state."""

    @abstractmethod
    async def act(self, action: AgentAction) -> Dict[str, Any]:
        """Execute the decided action and return the result."""

    async def run(self, context: AgentContext) -> Dict[str, Any]:
        """Full perception → decision → action cycle."""
        perception = await self.perceive(context)
        action = await self.decide(perception)
        return await self.act(action)
