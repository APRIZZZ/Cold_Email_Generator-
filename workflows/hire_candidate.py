from tools import email_utils


def run(ctx: dict):
    orchestrator = ctx["orchestrator"]
    org_profile = ctx["org_profile"]

    candidate_name = input("\nCandidate name: ").strip()
    if not candidate_name:
        print("Candidate name cannot be empty. Returning to menu.")
        return

    candidate_email = input("Candidate email: ").strip()
    if not email_utils.is_valid_email(candidate_email):
        print("That doesn't look like a valid email address. Cancelling.")
        return

    position = input("Position they're being hired for: ").strip()
    extra_details = input(
        "Any extra details to include (salary/start date/next steps), one line (optional): "
    ).strip()

    purpose = (
        f"Inform {candidate_name} they have been selected/hired for the position "
        f"of {position}. Additional details: {extra_details or 'none provided'}."
    )

    print("Generating offer email with writer/reviewer agents ...")
    result = orchestrator.generate_email(
        purpose=purpose,
        org_profile=org_profile,
        company_context={"company_name": candidate_name},
        email_type="hire_candidate",
    )

    _show_and_optionally_send(candidate_email, result)


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