import getpass

from config import ADMIN_USERNAME, ADMIN_PASSWORD, ORG_PROFILE
from rag.company_knowledge_base import CompanyKnowledgeBase
from tools.web_search import WebSearchTool
from agents.orchestrator import EmailOrchestrator

from workflows import request_service, provide_service, hire_candidate, reject_candidate, notification

MENU_TEXT = """
==================== MAIN MENU ====================
1. Request a service
2. Provide a service
3. Hire a candidate
4. Reject a candidate
5. Send a notification
0. Exit
=====================================================
"""


def login() -> bool:
    print("---- Admin Login ----")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        print(f"Welcome, {username}.\n")
        return True
    print("Invalid credentials.")
    return False


def build_context() -> dict:
    return {
        "org_profile": ORG_PROFILE,
        "rag_kb": CompanyKnowledgeBase(),
        "web_search": WebSearchTool(),
        "orchestrator": EmailOrchestrator(),
    }


def main():
    if not login():
        return

    ctx = build_context()

    handlers = {
        "1": request_service.run,
        "2": provide_service.run,
        "3": hire_candidate.run,
        "4": reject_candidate.run,
        "5": notification.run,
    }

    while True:
        print(MENU_TEXT)
        choice = input("Choose an option: ").strip()

        if choice == "0":
            print("Goodbye.")
            break

        handler = handlers.get(choice)
        if handler is None:
            print("That option isn't built yet, or invalid choice.")
            continue

        try:
            handler(ctx)
        except KeyboardInterrupt:
            print("\nCancelled.")
        except Exception as e:
            print(f"An error occurred while running this workflow: {e}")


if __name__ == "__main__":
    main()