"""
tests/test_provider_manager_health.py
======================================
Regression tests for ProviderState and ProviderInstance health semantics.

Verifies:
1. UNHEALTHY != HEALTHY
2. CONNECTED != necessarily HEALTHY (transport connected does not imply authorized/healthy)
3. Provider starts in REGISTERED state (adapter initialization != healthy)
4. Multi-provider dictionary health check handles provider-specific booleans (no falsy dict bug)
5. Stateless REST adapters without connect_fn do not falsely jump to CONNECTED when unhealthy
6. No secrets or API keys are exposed in provider representations
"""

import pytest
import asyncio
from app.utils.provider_manager import ProviderInstance, ProviderState, CircuitBreaker, CircuitState


def test_provider_states_distinct():
    """Prove UNHEALTHY != HEALTHY and all core states are distinct."""
    assert ProviderState.UNHEALTHY != ProviderState.HEALTHY
    assert ProviderState.CONNECTED != ProviderState.HEALTHY
    assert ProviderState.REGISTERED != ProviderState.CONNECTED
    assert ProviderState.REGISTERED != ProviderState.HEALTHY
    assert ProviderState.UNAVAILABLE != ProviderState.HEALTHY
    assert ProviderState.DEGRADED != ProviderState.HEALTHY


@pytest.mark.asyncio
async def test_connected_not_necessarily_healthy():
    """
    Prove that a provider can be transport-CONNECTED but UNHEALTHY
    if its health check / authorization check fails.
    """
    connect_called = False
    def mock_connect():
        nonlocal connect_called
        connect_called = True

    # Failing health check (e.g. invalid credentials or auth rejected)
    def mock_health():
        return False

    provider = ProviderInstance(
        name="test_broker",
        connect_fn=mock_connect,
        health_check_fn=mock_health,
    )

    assert provider.state == ProviderState.REGISTERED
    assert provider.healthy is False

    await provider.initialize()

    assert connect_called is True
    # The provider connected transport, but failed health check -> must be UNHEALTHY
    assert provider.state == ProviderState.UNHEALTHY
    assert provider.healthy is False
    assert provider.state != ProviderState.HEALTHY


@pytest.mark.asyncio
async def test_stateless_rest_adapter_unhealthy_on_failed_check():
    """
    For REST providers (e.g. OpenRouter) with no connect_fn:
    Initialization must NOT claim CONNECTED if health check fails.
    """
    def openrouter_health():
        return False

    provider = ProviderInstance(
        name="openrouter",
        connect_fn=None,
        health_check_fn=openrouter_health,
    )

    assert provider.state == ProviderState.REGISTERED
    await provider.initialize()

    assert provider.state == ProviderState.UNHEALTHY
    assert provider.healthy is False


@pytest.mark.asyncio
async def test_multi_provider_dict_health_check_parsing():
    """
    Prove that dictionary results like {'openrouter': False, 'gemini': True}
    are parsed per provider name rather than evaluating bool(dict) == True.
    """
    health_dict = {"openrouter": False, "gemini": True}

    provider = ProviderInstance(
        name="openrouter",
        connect_fn=None,
        health_check_fn=lambda: health_dict,
    )

    await provider.initialize()

    # In previous bug, bool(health_dict) evaluated to True.
    # With fix, provider correctly extracts health_dict['openrouter'] -> False
    assert provider.healthy is False
    assert provider.state == ProviderState.UNHEALTHY


@pytest.mark.asyncio
async def test_provider_becomes_healthy_only_when_verified():
    """
    Prove that a provider transitions to HEALTHY only when verified.
    """
    provider = ProviderInstance(
        name="verified_service",
        connect_fn=lambda: None,
        health_check_fn=lambda: True,
    )

    await provider.initialize()

    assert provider.healthy is True
    assert provider.state == ProviderState.HEALTHY


def test_no_secrets_in_provider_repr():
    """Ensure provider instance does not expose credentials in repr/str."""
    provider = ProviderInstance(
        name="openrouter",
        connect_fn=None,
        health_check_fn=lambda: False,
    )
    rep = repr(provider)
    s = str(provider)
    assert "sk-" not in rep and "sk-" not in s
    assert "Bearer" not in rep and "Bearer" not in s
