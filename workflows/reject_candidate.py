from tools import email_utils


def run(ctx: dict):

    orchestrator = ctx["orchestrator"]
    org_profile = ctx["org_profile"]

    candidate_name = input(
        "\nCandidate name: "
    ).strip()

    if not candidate_name:

        print(
            "Candidate name cannot be empty. "
            "Returning to menu."
        )

        return

    candidate_email = input(
        "Candidate email: "
    ).strip()

    if not email_utils.is_valid_email(
        candidate_email
    ):

        print(
            "That doesn't look like a valid email address. "
            "Cancelling."
        )

        return

    position = input(
        "Position they applied for: "
    ).strip()

    if not position:

        print(
            "Position cannot be empty. "
            "Returning to menu."
        )

        return

    reason_note = input(
        "Optional one-line note on reason/feedback "
        "(leave blank if none): "
    ).strip()

    if reason_note:

        feedback_text = reason_note

    else:

        feedback_text = (
            "No specific reason should be provided. "
            "Do not invent one."
        )

    purpose = f"""
Candidate name: {candidate_name}

Position applied for: {position}

Decision:
The candidate was not selected for this position.

Additional feedback:
{feedback_text}

Write a respectful and professional candidate rejection email.

Thank the candidate for their time and interest.
Clearly communicate that they were not selected.

If no specific feedback was provided, do not invent a reason.
Do not mention facts about the candidate that were not provided.
Do not turn this into a sales or partnership email.
"""

    print(
        "\nGenerating rejection email with "
        "writer/reviewer agents ..."
    )

    result = orchestrator.generate_email(
        purpose=purpose,
        org_profile=org_profile,

        # The candidate is the recipient.
        # We use this only to provide the candidate's name.
        company_context={
            "company_name": candidate_name
        },

        email_type="reject_candidate",
    )

    _show_and_optionally_send(
        candidate_email,
        result
    )


def _show_and_optionally_send(
    target_email: str,
    result: dict
):

    subject = result["subject"]
    body = result["body"]

    while True:

        print("\n" + "=" * 60)
        print(f"To: {target_email}")
        print(f"Subject: {subject}")
        print("-" * 60)
        print(body)
        print("=" * 60)

        send_now = input(
            "\nSend this email now? (y/n): "
        ).strip().lower()

        if send_now == "y":

            email_utils.send_email(
                target_email,
                subject,
                body
            )

            return

        print(
            "\nOkay, not sending yet. "
            "What would you like to do?"
        )

        print(
            "  1. Make changes myself before sending"
        )

        print(
            "  2. Changed my mind -- don't send this email"
        )

        next_choice = input(
            "Choose 1 or 2: "
        ).strip()

        if next_choice == "1":

            new_subject = input(
                f"\nEdit subject "
                f"(leave blank to keep: '{subject}'): "
            ).strip()

            if new_subject:

                subject = new_subject

            print(
                "\nEdit body. Type your new body, "
                "then type END on its own line when done."
            )

            print(
                "(Leave the first line blank and just type END "
                "to keep the current body.)"
            )

            lines = []

            while True:

                line = input()

                if line.strip() == "END":

                    break

                lines.append(line)

            if lines:

                body = "\n".join(lines)

        else:

            print(
                "Email discarded. Not sent."
            )

            return