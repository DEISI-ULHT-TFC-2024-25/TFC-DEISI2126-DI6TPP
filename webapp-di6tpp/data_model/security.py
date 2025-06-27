from passlib.hash import argon2

secure_argon2 = argon2.using(
    time_cost=4,         # raise the computational cost (4 iterations)
    memory_cost=131072,  # 128 MB of RAM (strong value)
    parallelism=2        # two threads at the same time
)

def hash_password(password: str) -> str:
    """
    Hashes a password using Argon2 (excellent against brute-force and GPU attacks).
    """
    return secure_argon2.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a password against its Argon2 hash.
    """
    return secure_argon2.verify(plain_password, hashed_password)