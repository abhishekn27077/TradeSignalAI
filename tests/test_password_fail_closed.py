"""
Phase 74 Regression Tests — TS-011 Password Fail-Closed

These tests verify that TS-011 (Plaintext Password Fallback) is fixed:
- Password functions raise RuntimeError when dependencies unavailable
- No plaintext is ever returned as a fallback
- Authentication fails closed, not open
"""
import pytest
import sys


class TestPasswordFailClosed:
    """TS-011: Password functions must fail closed, never return plaintext."""

    def test_verify_password_fails_closed_no_jose(self):
        """verify_password must raise RuntimeError when jose unavailable."""
        from app.auth.security import verify_password
        import app.auth.security as security
        original_has_jose = security._has_jose

        try:
            security._has_jose = False
            with pytest.raises(RuntimeError) as exc_info:
                security.verify_password("test", "hash")
            assert "Cannot verify password" in str(exc_info.value)
        finally:
            security._has_jose = original_has_jose

    def test_get_password_hash_fails_closed_no_jose(self):
        """get_password_hash must raise RuntimeError when jose unavailable, not return plaintext."""
        from app.auth.security import get_password_hash
        import app.auth.security as security
        original_has_jose = security._has_jose

        try:
            security._has_jose = False
            with pytest.raises(RuntimeError) as exc_info:
                security.get_password_hash("test_password")
            assert "authentication libraries not available" in str(exc_info.value)
        finally:
            security._has_jose = original_has_jose

    def test_verify_token_fails_closed_no_jose(self):
        """verify_token must raise RuntimeError when jose unavailable."""
        from app.auth.security import verify_token
        import app.auth.security as security
        original_has_jose = security._has_jose

        try:
            security._has_jose = False
            with pytest.raises(RuntimeError) as exc_info:
                security.verify_token("some_token")
            assert "Cannot verify token" in str(exc_info.value)
        finally:
            security._has_jose = original_has_jose

    def test_no_plaintext_fallback_exists(self):
        """Verify no code path returns plaintext password as fallback.

        Scan the security.py file for any 'return password' statement outside of
        test/helpers.
        """
        import ast

        with open('app/auth/security.py', 'r') as f:
            source = f.read()

        # Parse the AST to find all 'return' statements
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Return):
                if isinstance(node.value, ast.Name) and node.value.id == 'password':
                    pytest.fail("Found 'return password' fallback - violates fail-closed requirement")


class TestPasswordDependencyCheck:
    """Verify password dependencies are installed in production."""

    def test_jose_and_passlib_available(self):
        """Ensure jose and passlib are available for secure password handling."""
        try:
            from jose import JWTError, jwt
            from passlib.context import CryptContext
            assert True
        except ImportError as e:
            pytest.fail(f"Authentication dependencies missing: {e}")