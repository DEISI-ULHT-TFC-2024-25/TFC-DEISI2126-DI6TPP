import requests

url = f"http://__HOST_IP__:8080/WebGoat/register.mvc"

payload = f"username=__USERNAME__&password=__PASSWORD__&matchingPassword=__PASSWORD__&agree=agree"
headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

session = requests.Session()
response = session.post(url, headers=headers, data=payload)

if response.status_code == 200:
    print("Register was successful.")
else:
    print(response.status_code)
