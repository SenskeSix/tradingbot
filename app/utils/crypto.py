import hmac
import hashlib


def verify_hmac(body: bytes, secret: str, signature: str) -> bool:
    computed = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)
