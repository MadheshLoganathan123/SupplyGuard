"""
LLM Service — Manages LLM calls for agent reasoning with structured outputs.
Uses OpenAI-compatible API (configurable via environment).
"""

import json
import os
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.core.config import settings


class StructuredToolCall(BaseModel):
    """Structured tool invocation by LLM."""
    tool_name: str = Field(..., description="Name of the tool to call")
    params: dict[str, Any] = Field(..., description="Tool parameters")


class AgentDecision(BaseModel):
    """LLM-generated agent decision with reasoning."""
    reasoning: str = Field(..., description="Agent's reasoning for the decision")
    action_type: str = Field(..., description="Type of action (e.g., 'reroute', 'negotiate', 'allocate')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    tools: list[StructuredToolCall] = Field(default_factory=list, description="Tools to call")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class LLMService:
    """Service for LLM-powered agent reasoning."""

    def __init__(self):
        self.settings = settings
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.timeout = 30.0

    async def reason(
        self,
        context: dict[str, Any],
        system_prompt: str,
        user_prompt: str,
    ) -> AgentDecision:
        """
        Call LLM for structured agent reasoning.

        Args:
            context: Agent context (state, incidents, profiles, etc.)
            system_prompt: System-level instructions for the agent role
            user_prompt: User/situation-specific prompt

        Returns:
            AgentDecision with reasoning, action_type, confidence, and tools
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.7,
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                data = response.json()

                # Extract JSON from response content
                content = data["choices"][0]["message"]["content"]
                decision_json = json.loads(content)

                return AgentDecision(**decision_json)
        except httpx.HTTPError as e:
            # Fallback to heuristic-only decision if LLM fails
            return AgentDecision(
                reasoning="LLM unavailable; using heuristic fallback",
                action_type="heuristic_fallback",
                confidence=0.5,
                tools=[],
                metadata={"error": str(e), "context_keys": list(context.keys())},
            )

    async def generate_agent_prompt(
        self,
        agent_role: str,
        sector_state: dict[str, Any],
        incidents: list[dict[str, Any]],
    ) -> str:
        """
        Generate a detailed prompt for the agent based on sector state and incidents.

        Args:
            agent_role: Role of the agent (e.g., "logistics", "sourcing", "negotiation")
            sector_state: Current state of the sector (shipments, inventory, nodes)
            incidents: List of active incidents

        Returns:
            Formatted prompt for LLM
        """
        incident_summary = "\n".join(
            [f"- {inc.get('type', 'unknown')}: {inc.get('description', '')}" for inc in incidents]
        )

        prompt = f"""You are a {agent_role} agent in a supply chain network.

**Current Sector State:**
{json.dumps(sector_state, indent=2)}

**Active Incidents:**
{incident_summary or "None"}

Analyze the situation and provide:
1. **reasoning**: Your thought process
2. **action_type**: The type of action (e.g., 'reroute', 'allocate', 'negotiate')
3. **confidence**: A score 0-1 of your confidence in this action
4. **tools**: A list of tools to invoke with their parameters
5. **metadata**: Any additional context (e.g., alternative options, risks)

Return as JSON.
"""
        return prompt

    async def evaluate_intervention(
        self,
        incident_type: str,
        current_state: dict[str, Any],
        proposed_action: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Use LLM to evaluate if a proposed intervention is appropriate.

        Args:
            incident_type: Type of incident
            current_state: Current supply chain state
            proposed_action: Proposed intervention action

        Returns:
            Evaluation with approval_score, rationale, and risks
        """
        prompt = f"""Evaluate this proposed intervention:

**Incident:** {incident_type}
**Current State:** {json.dumps(current_state, indent=2)}
**Proposed Action:** {json.dumps(proposed_action, indent=2)}

Provide:
1. **approval_score**: 0-1 score for approval likelihood
2. **rationale**: Why you approve/disapprove
3. **risks**: List of potential risks
4. **alternatives**: Alternative actions to consider

Return as JSON.
"""

        system_prompt = "You are an expert supply chain analyst evaluating intervention decisions."

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.5,
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except httpx.HTTPError:
            # Fallback evaluation
            return {
                "approval_score": 0.5,
                "rationale": "LLM unavailable; neutral recommendation",
                "risks": ["System degradation"],
                "alternatives": [],
            }
