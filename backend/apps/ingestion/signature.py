"""Webhook signature verification (constant-time)."""

import hashlib
import hmac


def verify_github_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = signature_header[7:]
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected)


def verify_gitlab_token(secret: str, token_header: str | None) -> bool:
    if not token_header:
        return False
    return hmac.compare_digest(secret, token_header)
