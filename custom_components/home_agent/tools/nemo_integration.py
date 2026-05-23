"""NeMo Guardrails integration for Home Agent tool handler.

This module integrates the GuardrailsValidator with the ToolHandler
to enforce PAHA behavioral policies before tool execution.

Per AGENTS.md:
- PAHA is a constrained semantic translator (not a chatbot or reasoner)
- Validation happens at the tool validation layer
"""

from __future__ import annotations

import logging
from typing import Any

from .nemo_guardrails import GuardrailsValidator

_LOGGER = logging.getLogger(__name__)


class NeMoToolValidator(GuardrailsValidator):
    """NeMo-enhanced tool validator for PAHA.

    Extends GuardrailsValidator with NeMo-specific integrations.
    Currently acts as a wrapper for the base validator.

    Attributes:
        guardrails: The underlying GuardrailsValidator instance
        enabled: Whether validation is active
    """

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the NeMo tool validator.

        Args:
            enabled: Whether to enforce guardrails (default: True)
        """
        super().__init__(enabled=enabled)
        self._guardrails = self

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
        return self._guardrails.validate_tool_call(tool_name, parameters)

    def validate_tool_calls_batch(
        self,
        tool_calls: list[dict[str, Any]],
    ) -> list[tuple[bool, str | None]]:
        """Validate multiple tool calls against the behavioral policy.

        Args:
            tool_calls: List of tool call dictionaries with 'name' and 'parameters'

        Returns:
            List of (is_valid, error_message) tuples for each call
        """
        results = []
        for call in tool_calls:
            tool_name = call.get("name", "")
            parameters = call.get("parameters", {})
            is_valid, error = self.validate_tool_call(tool_name, parameters)
            results.append((is_valid, error))
        return results

    def filter_valid_calls(
        self,
        tool_calls: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter out invalid tool calls based on guardrails.

        Args:
            tool_calls: List of tool call dictionaries

        Returns:
            List of only valid tool calls
        """
        valid_calls = []
        for call in tool_calls:
            is_valid, _ = self.validate_tool_call(
                call.get("name", ""),
                call.get("parameters", {}),
            )
            if is_valid:
                valid_calls.append(call)
        return valid_calls

    def get_policy_summary(self) -> dict[str, Any]:
        """Get a summary of the current guardrails policy.

        Returns:
            Dictionary containing policy summary
        """
        return {
            "enabled": self._enabled,
            "allowed_tools": ["ha_control", "ha_query", "query_external_llm"],
            "constraints": [
                "single_shot_or_punt",
                "no_multi_step_planning",
                "no_long_form_prose",
                "no_memory_consolidation",
            ],
        }
