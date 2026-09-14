from tools import email_utils


def run(ctx: dict):
    orchestrator = ctx["orchestrator"]
    org_profile = ctx["org_profile"]

    notif_type = input(
        "\nWhat kind of notification is this? (e.g. 'new position opened', 'sale/promotion', 'general announcement'): "
    ).strip()
    if not notif_type:
        print("Notification type cannot be empty. Returning to menu.")
        return

    details = input("Give the details in one or two lines: ").strip()

    recipients_raw = input("Enter recipient email(s), comma-separated: ").strip()
    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    recipients = [r for r in recipients if email_utils.is_valid_email(r)]

    if not recipients:
        print("No valid recipient emails provided. Cancelling.")
        return

    purpose = f"Notification type: {notif_type}. Details: {details}"

    print("Generating notification email with writer/reviewer agents ...")
    result = orchestrator.generate_email(
        purpose=purpose,
        org_profile=org_profile,
        company_context=None,
        email_type="notification",
    )

    _show_and_optionally_send(recipients, result)


def _show_and_optionally_send(recipients: list, result: dict):
    subject = result["subject"]
    body = result["body"]

    while True:
        print("\n" + "=" * 60)
        print(f"To: {', '.join(recipients)}")
        print(f"Subject: {subject}")
        print("-" * 60)
        print(body)
        print("=" * 60)

        send_now = input(f"\nSend this to all {len(recipients)} recipient(s) now? (y/n): ").strip().lower()

        if send_now == "y":
            for r in recipients:
                success = email_utils.send_email(r, subject, body)
                print(f"  -> {r}: {'sent' if success else 'failed/printed'}")
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