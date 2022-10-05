import os
import base64
import hashlib
import random

def generate_code_verifier(n_bytes=64):
    """Python-compatible PKCE code verifier shamelessly borrowed from
    https://github.com/openstack/deb-python-oauth2client/blob/master/oauth2client/_pkce.py."""
    verifier = base64.urlsafe_b64encode(os.urandom(n_bytes)).rstrip(b'=')
    # https://tools.ietf.org/html/rfc7636#section-4.1
    # minimum length of 43 characters and a maximum length of 128 characters.
    if len(verifier) < 43:
        raise ValueError("Verifier too short. n_bytes must be > 30.")
    elif len(verifier) > 128:
        raise ValueError("Verifier too long. n_bytes must be < 97.")
    else:
        return verifier


def get_code_challenge(verifier):
    """Generate a code challenge based on the code verifier"""
    digest = hashlib.sha256(verifier).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=')

def random_string(length=41):
    chars = "abcdefghijklmnopqrstuvwxyz123456789";
    result = [random.choice(chars) for _ in range(0,length)]
    return ''.join(result)

def get_nonce(length=41):
    return random_string(length)

def get_state(length=41):
    return random_string(length)

if __name__ == '__main__':
    CODE_VERIFIER = generate_code_verifier()
    CODE_CHALLENGE = get_code_challenge(CODE_VERIFIER)
    NONCE = get_nonce()
    STATE = get_state()
    # CODE_VERIFIER=CODE_VERIFIER.decode('utf-8')
    # CODE_CHALLENGE=CODE_CHALLENGE.decode('utf-8')
    print('----------------------------------------------------------------')
    print(f'CODE_VERIFIER -> {CODE_VERIFIER}')
    print(f'LEN CODE_VERIFIER -> {len(CODE_VERIFIER)}')
    print('----------------------------------------------------------------')

    print(f'CODE_CHALLENGE -> {CODE_CHALLENGE}')
    print(f'LEN CODE_CHALLENGE -> {len(CODE_CHALLENGE)}')
    print('----------------------------------------------------------------')

    print(f'NONCE -> {NONCE}')
    print(f'LEN NONCE-> {len(NONCE)}')
    print('----------------------------------------------------------------')

    print(f'STATE -> {STATE}')
    print(f'LEN STATE-> {len(STATE)}')
