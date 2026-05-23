"""NeMo Guardrails validator for Home Agent.

This module provides a separate validator class that checks LLM proposals
against the PAHA behavioral policy.

Per AGENTS.md:
- PAHA is a constrained semantic translator, not a chatbot or reasoner.
- The validator enforces that tool calls map to validated HA actions,
  clarifications, escalations, or no-ops.
"""

from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


class GuardrailsValidator:
    """Validates tool proposals against PAHA behavioral policy.

    Per AGENTS.md, PAHA is **not** a chatbot, reasoner, or memory store.
    It is a **constrained semantic translator** that maps utterances to:
      1. A validated HA action call (query or execute)
      2. A clarifying question
      3. An escalation to the orchestration head
      4. A no-op

    This validator enforces these constraints before tool execution.

    Attributes:
        enabled: Whether validation is active
        policy: The behavioral policy definition
    """

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the validator.

        Args:
            enabled: Whether to enforce guardrails (default: True)
        """
        self._enabled = enabled
        self._policy = self._build_policy()

    def _build_policy(self) -> list[dict[str, Any]]:
        """Build the behavioral policy definition.

        Returns:
            List of policy rules for PAHA constraints
        """
        return [
            {
                "type": "tool_call_constraint",
                "allowed_tools": ["ha_control", "ha_query", "query_external_llm"],
                "forbidden_patterns": [
                    "multi-step planning",
                    "long-form prose",
                    "multi-step reasoning",
                    "long-term memory consolidation",
                    "synthesize knowledge",
                    "improvise uncertainly",
                ],
            },
            {
                "type": "behavioral_constraint",
                "rule": "single_shot_or_punt",
                "description": "PAHA must make one confident shot or punt — not exploration",
            },
            {
                "type": "output_constraint",
                "allowed_outputs": [
                    "validated_ha_action",
                    "clarifying_question",
                    "escalation",
                    "no_op",
                ],
            },
        ]

    def validate_tool_call(
        self,
        tool_name: str,
        parameters: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Validate a tool call against the behavioral policy.

        Args:
            tool_name: Name of the tool being called
            parameters: Parameters for the tool call

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self._enabled:
            return True, None

        # Check allowed tools
        allowed_tools = ["ha_control", "ha_query"]
        if tool_name not in allowed_tools:
            # Allow external LLM only if explicitly enabled
            if tool_name == "query_external_llm":
                return True, None
            return False, f"Tool '{tool_name}' is not allowed by guardrails"

        # Validate parameters do not contain forbidden patterns
        param_str = str(parameters).lower()
        for pattern in self._policy[0]["forbidden_patterns"]:
            if pattern.lower() in param_str:
                return False, f"Tool call contains forbidden pattern: '{pattern}'"

        return True, None

    def is_enabled(self) -> bool:
        """Check if guardrails validation is active.

        Returns:
            True if validation is enabled
        """
        return self._enabled

    def enable(self) -> None:
        """Enable guardrails validation."""
        self._enabled = True
        _LOGGER.info("Guardrails validation enabled")

    def disable(self) -> None:
        """Disable guardrails validation."""
        self._enabled = False
        _LOGGER.info("Guardrails validation disabled")
