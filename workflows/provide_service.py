from tools import email_utils
from agents.llm_client import complete


def _clean_search_query(purpose: str) -> str:
    """Turns a raw admin-typed purpose into a clean search-engine query,
    preserving any location mentioned."""
    system = (
        "You convert a business pitch/target description into a short web "
        "search query for finding companies that would be good prospects. "
        "Preserve any location mentioned. "
        "Reply with ONLY the search query, nothing else, no quotes."
    )
    query = complete(system, purpose, max_tokens=30, temperature=0.2)
    return query.strip().strip('"')


def run(ctx: dict):
    rag_kb = ctx["rag_kb"]
    web_search = ctx["web_search"]
    orchestrator = ctx["orchestrator"]
    org_profile = ctx["org_profile"]

    purpose = input(
        "\nDescribe the service you want to pitch, and to what kind of company (one line): "
    ).strip()
    if not purpose:
        print("Purpose cannot be empty. Returning to menu.")
        return

    print("\nDo you have a specific company in mind?")
    print("  1. Yes, I'll specify the company")
    print("  2. No, search the web for a suitable prospect")
    print("  3. I already have the recipient's email address")
    sub_choice = input("Choose 1, 2, or 3: ").strip()

    target_email = None
    company_name = None

    if sub_choice == "1":
        company_name = input("Enter the company name: ").strip()
        target_email = _resolve_email(web_search, company_name, None)

    elif sub_choice == "3":
        company_name = input("Company name (for context in the email, optional): ").strip() or "the recipient"
        manual_email = input("Enter the recipient's email address: ").strip()
        if email_utils.is_valid_email(manual_email):
            target_email = manual_email
        else:
            print("That doesn't look like a valid email address. Cancelling.")
            return

    elif sub_choice == "2":
        search_query = _clean_search_query(purpose)
        print(f"\nSearching the web for: {search_query} ...")
        candidates = web_search.search_companies_for_service(search_query)
        if not candidates:
            print("No candidates found via web search. Returning to menu.")
            return

        remaining = candidates.copy()
        while remaining and not target_email:
            print("\nCandidates:")
            for i, c in enumerate(remaining, 1):
                print(f"  {i}. {c['name']}  ({c['url']})")
            idx = input(f"Pick one [1-{len(remaining)}], or 0 to cancel: ").strip()
            if idx == "0":
                print("Cancelled.")
                return
            try:
                chosen = remaining[int(idx) - 1]
            except (ValueError, IndexError):
                print("Invalid choice, try again.")
                continue

            company_name = chosen["name"]
            target_email = _resolve_email(web_search, company_name, chosen["url"])

            if not target_email:
                print(f"Could not find an email for '{company_name}'.")
                remaining.remove(chosen)
                if remaining:
                    retry = input("Try a different candidate from the list? (y/n): ").strip().lower()
                    if retry != "y":
                        return
                else:
                    print("No more candidates left. Returning to menu.")
                    return

    else:
        print("Invalid choice. Returning to menu.")
        return

    if not target_email:
        print("No recipient email available. Cancelling.")
        return

    print("Retrieving company context from knowledge base (RAG) ...")
    company_context = rag_kb.find_by_name(company_name) or {"company_name": company_name}

    print("Generating pitch email with writer/reviewer agents ...")
    result = orchestrator.generate_email(
        purpose=purpose,
        org_profile=org_profile,
        company_context=company_context,
        email_type="provide_service",
    )

    _show_and_optionally_send(target_email, result)


def _resolve_email(web_search, company_name: str, website):
    print(f"Looking up a contact email for '{company_name}' ...")
    email = web_search.find_company_email(company_name, website)
    if email:
        print(f"Found email: {email}")
        return email

    manual = input(
        f"Could not auto-discover an email for '{company_name}'. "
        f"Enter one manually (or leave blank to skip): "
    ).strip()
    if manual and email_utils.is_valid_email(manual):
        return manual
    if manual:
        print("That doesn't look like a valid email.")
    return None


def _show_and_optionally_send(target_email: str, result: dict):
    subject = result["subject"]
    body = result["body"]

    while True:
        print("\n" + "=" * 60)
        print(f"To: {target_email}")
        print(f"Subject: {subject}")
        print("-" * 60)
        print(body)
        print("=" * 60)

        send_now = input("\nSend this email now? (y/n): ").strip().lower()

        if send_now == "y":
            email_utils.send_email(target_email, subject, body)
            return

        print("\nOkay, not sending yet. What would you like to do?")
        print("  1. Make changes myself before sending")
        print("  2. Changed my mind -- don't send this email")
        next_choice = input("Choose 1 or 2: ").strip()

        if next_choice == "1":
            new_subject = input(f"\nEdit subject (leave blank to keep: '{subject}'): ").strip()
            if new_subject:
                subject = new_subject

            print("\nEdit body. Type your new body, then type END on its own line when done.")
            print("(Leave the very first line blank and just type END to keep the current body.)")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            if lines:
                body = "\n".join(lines)

        else:
            print("Email discarded. Not sent.")
            return