"""Test conversation session manager."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.home_agent.conversation_session import (
    DEFAULT_SESSION_TIMEOUT,
    ConversationSessionManager,
)


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
