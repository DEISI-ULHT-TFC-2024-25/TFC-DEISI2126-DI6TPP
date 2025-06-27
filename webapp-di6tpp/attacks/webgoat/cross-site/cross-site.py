import requests

webgoat_url = "http://__HOST_IP__:8080/WebGoat/XSS/attack"
payload = "__PAYLOAD__"

data = {
    "inputField": payload
}

response = requests.post(webgoat_url, data=data)
if response.status_code == 200:
    print("[+] XSS attack payload submitted successfully!")
else:
    print(f"[-] Failed to submit payload. Status code: {response.status_code}")

