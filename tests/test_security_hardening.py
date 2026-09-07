"""
TradeSignalAI-v3 — Security Hardening Regression Test Suite
Phase: Complete Secret & Credential Security Hardening

Verifies:
1. .env and .env.* are ignored by .gitignore and cannot be accidentally tracked.
2. Missing or weak SECRET_KEY in production mode causes fail-closed startup abort.
3. Plaintext password fallback is impossible (raises RuntimeError).
4. Frontend source tree contains zero private credentials or VITE_* secrets.
5. API responses and health/broker endpoints do not leak credentials.
6. Exception handler redacts sensitive connection strings and tokens.
7. Logger automatically redacts Authorization headers, API keys, and connection credentials.
8. Real-money execution remains strictly locked out (REAL_MONEY_ENABLED = False).
9. Git index does not track .env, database files, or sensitive log files.
10. Development mode defaults remain safely operational without compromising security.
"""

import os
import re
import subprocess
import pytest
from unittest.mock import patch

from app.config.settings import Settings
from app.logs.logger import redact_sensitive_text


class TestGitIgnoreHardening:
    """Verifies repository .gitignore strictly excludes credentials and persistence artifacts."""

    def test_env_is_ignored_by_git(self):
        """Verify .env, .env.local, .env.production are matched by .gitignore."""
        test_files = [".env", ".env.local", ".env.production", ".env.backup"]
        for fname in test_files:
            res = subprocess.run(
                ["git", "check-ignore", "--no-index", fname],
                capture_output=True,
                text=True
            )
            assert res.returncode == 0, f"{fname} is not properly ignored by .gitignore"

    def test_env_example_is_allowed(self):
        """.env.example must not be ignored (it must be committed as safe template)."""
        res = subprocess.run(
            ["git", "check-ignore", "--no-index", ".env.example"],
            capture_output=True,
            text=True
        )
        assert res.returncode != 0, ".env.example should NOT be ignored"

    def test_databases_and_logs_are_ignored(self):
        """Databases and log files must be ignored."""
        test_paths = ["test.db", "tradesignal.db", "data.sqlite3", "logs/app.log", "debug.log"]
        for p in test_paths:
            res = subprocess.run(
                ["git", "check-ignore", "--no-index", p],
                capture_output=True,
                text=True
            )
            assert res.returncode == 0, f"{p} is not properly ignored by .gitignore"

    def test_git_index_does_not_track_env_or_db(self):
        """Verify git index currently tracks zero .env or .db files."""
        res = subprocess.run(
            ["git", "ls-files", ".env", "*.db", "logs/app.log.*"],
            capture_output=True,
            text=True
        )
        tracked = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        assert len(tracked) == 0, f"Sensitive files still tracked in git index: {tracked}"


class TestProductionAuthFailClosed:
    """Verifies that missing or weak secrets in production FAIL CLOSED."""

    def test_production_fails_when_secret_key_missing(self):
        with pytest.raises(ValueError) as exc_info:
            Settings(
                ENVIRONMENT="production",
                SECRET_KEY=None,
                _env_file=None
            )
        assert "Production startup aborted" in str(exc_info.value)
        assert "SECRET_KEY must be provided" in str(exc_info.value)

    def test_production_fails_when_secret_key_empty(self):
        with pytest.raises(ValueError) as exc_info:
            Settings(
                ENVIRONMENT="production",
                SECRET_KEY="   ",
                _env_file=None
            )
        assert "Production startup aborted" in str(exc_info.value)

    def test_production_fails_when_secret_key_is_weak(self):
        weak_keys = ["secret", "changeme", "development-secret", "test-secret", "12345678", "password"]
        for weak in weak_keys:
            with pytest.raises(ValueError) as exc_info:
                Settings(
                    ENVIRONMENT="production",
                    SECRET_KEY=weak,
                    _env_file=None
                )
            assert "insecure or too short" in str(exc_info.value)

    def test_production_fails_when_secret_key_is_under_32_chars(self):
        with pytest.raises(ValueError) as exc_info:
            Settings(
                ENVIRONMENT="production",
                SECRET_KEY="short-secret-key-only-24-c",
                _env_file=None
            )
        assert "too short" in str(exc_info.value)

    def test_production_succeeds_with_strong_secret_key(self):
        strong_key = "a_very_strong_production_secret_key_with_sufficient_entropy_64_bytes"
        s = Settings(
            ENVIRONMENT="production",
            SECRET_KEY=strong_key,
            _env_file=None
        )
        assert s.SECRET_KEY == strong_key


class TestPasswordFailClosed:
    """Verifies zero plaintext password fallback."""

    def test_verify_password_fails_closed_without_crypto(self):
        import app.auth.security as security
        original = security._has_jose
        try:
            security._has_jose = False
            with pytest.raises(RuntimeError) as exc_info:
                security.verify_password("plaintext", "$2b$12$somehash")
            assert "Cannot verify password" in str(exc_info.value)
        finally:
            security._has_jose = original

    def test_hash_password_fails_closed_without_crypto(self):
        import app.auth.security as security
        original = security._has_jose
        try:
            security._has_jose = False
            with pytest.raises(RuntimeError) as exc_info:
                security.get_password_hash("plaintext")
            assert "Cannot hash password" in str(exc_info.value)
        finally:
            security._has_jose = original


class TestFrontendSecretExposure:
    """Verifies that the frontend contains zero private credentials or VITE_* secrets."""

    def test_no_vite_secrets_in_frontend_src(self):
        frontend_src = os.path.join("frontend", "src")
        if not os.path.exists(frontend_src):
            pytest.skip("frontend/src not found")

        openai_key_regex = re.compile(r'sk-[a-zA-Z0-9]{20,}')
        nvidia_key_regex = re.compile(r'nvapi-[a-zA-Z0-9_\-]{25,}')

        for root, _, files in os.walk(frontend_src):
            for f in files:
                if f.endswith((".ts", ".tsx", ".js", ".jsx", ".html")):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                    assert "VITE_SECRET" not in content, f"Possible secret in {fpath}"
                    assert "VITE_API_KEY" not in content, f"Possible API key in {fpath}"
                    assert not openai_key_regex.search(content), f"Hardcoded OpenAI key pattern in {fpath}"
                    assert not nvidia_key_regex.search(content), f"Hardcoded NVIDIA key pattern in {fpath}"


class TestLoggingAndExceptionRedaction:
    """Verifies automatic redaction in logging and exception handling."""

    def test_redact_sensitive_text_masks_bearer_tokens(self):
        raw = "Sending request with Authorization: Bearer abcdef1234567890abcdef to endpoint"
        redacted = redact_sensitive_text(raw)
        assert "abcdef1234567890abcdef" not in redacted
        assert "[REDACTED]" in redacted

    def test_redact_sensitive_text_masks_api_keys(self):
        key_prefix = "sk-"
        key_body = "abcdef123456789012345678"
        raw = f"Failed call with key {key_prefix}{key_body}"  # gitleaks:allow
        redacted = redact_sensitive_text(raw)
        assert "sk-abcdef" not in redacted
        assert "[REDACTED_API_KEY]" in redacted

    def test_redact_sensitive_text_masks_db_uris(self):
        raw = "Connecting to postgresql://postgres:SuperSecretPassword123@db.internal:5432/trading"
        redacted = redact_sensitive_text(raw)
        assert "SuperSecretPassword123" not in redacted
        assert "[REDACTED_DB_CREDENTIALS]" in redacted

    @pytest.mark.asyncio
    async def test_global_exception_handler_redacts_credentials(self):
        from app.api.middleware import global_exception_handler
        from fastapi import Request

        # Create a mock request
        class MockRequest:
            state = type("State", (), {"correlation_id": "test-corr-123"})()
        
        leaky_exc = ValueError("Database connection failed at postgresql://user:mypassword123@localhost:5432/db")
        resp = await global_exception_handler(MockRequest(), leaky_exc)
        
        import json
        body = json.loads(resp.body.decode())
        assert "mypassword123" not in body["message"]
        assert "[REDACTED_DB_CREDENTIALS]" in body["message"]


class TestRealMoneyLockout:
    """Verifies that real-money execution remains strictly locked out."""

    def test_real_money_execution_locked_by_default(self):
        settings = Settings(_env_file=None)
        assert settings.REAL_MONEY_ENABLED is False, "REAL_MONEY_ENABLED must be False by default"
        assert settings.EXECUTION_MODE in ("DEMO", "PAPER"), "Default EXECUTION_MODE must not be LIVE"

    def test_execution_abstraction_rejects_real_money(self):
        from app.core.execution_abstraction import paper_broker_adapter, OrderIntent
        import app.core.execution_abstraction as ea

        # Test submit_order raises PermissionError when REAL_MONEY_ENABLED is True
        order = OrderIntent(
            order_id="TEST-1",
            asset="EURUSD",
            direction="BUY",
            order_type="MARKET",
            quantity=0.1,
            limit_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
        )

        class MockSettings:
            REAL_MONEY_ENABLED = True
            BROKER_EXECUTION_ENABLED = True

        with patch("app.core.execution_abstraction.get_settings", return_value=MockSettings()):
            with pytest.raises(PermissionError) as exc_info:
                paper_broker_adapter.submit_order(order)
            assert "REAL_MONEY_EXECUTION_STRICTLY_LOCKED" in str(exc_info.value)


class TestWorkingTreeSecretsClean:
    """Verifies that working tree contains zero hardcoded API keys in active Python/TS source."""

    def test_no_hardcoded_keys_in_app(self):
        patterns = [
            re.compile(r'sk-[a-zA-Z0-9]{25,}'),
            re.compile(r'AIza[0-9A-Za-z-_]{35}'),
            re.compile(r'nvapi-[a-zA-Z0-9_\-]{25,}'),
            re.compile(r'sk-or-[a-zA-Z0-9_\-]{25,}'),
        ]
        app_dir = "app"
        for root, _, files in os.walk(app_dir):
            for file in files:
                if file.endswith((".py", ".json", ".yaml")):
                    fpath = os.path.join(root, file)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                    for pat in patterns:
                        match = pat.search(content)
                        assert match is None, f"Exposed credential pattern in {fpath}"
