import re
from typing import Dict, Optional, Tuple

from agents.writer_agent import WriterAgent
from agents.reviewer_agent import ReviewerAgent
from config import MAX_REVIEW_ITERATIONS


def parse_subject_body(raw: str) -> Tuple[str, str]:

    subject_match = re.search(
        r"SUBJECT:\s*(.+)",
        raw
    )

    body_match = re.search(
        r"BODY:\s*(.+)",
        raw,
        re.DOTALL
    )

    subject = (
        subject_match.group(1).strip()
        if subject_match
        else "Regarding a potential collaboration"
    )

    body = (
        body_match.group(1).strip()
        if body_match
        else raw.strip()
    )

    return subject, body


class EmailOrchestrator:

    def __init__(self):

        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()


    def generate_email(
        self,
        purpose: str,
        org_profile: Dict,
        company_context: Optional[Dict] = None,
        email_type: str = "request_service",
        verbose: bool = True,
    ) -> Dict:

        # --------------------------------------------------
        # 1. Generate initial draft
        # --------------------------------------------------

        draft = self.writer.draft(
            purpose,
            org_profile,
            company_context,
            email_type
        )


        # --------------------------------------------------
        # 2. Review and revise
        # --------------------------------------------------

        for iteration in range(
            1,
            MAX_REVIEW_ITERATIONS + 1
        ):

            verdict = self.reviewer.review(
                draft,
                company_context
            )


            if verbose:

                print(
                    f"  [reviewer pass {iteration}] "
                    f"approved={verdict['approved']}"
                )


            if verdict["approved"]:

                break


            # IMPORTANT:
            # Pass email_type and purpose during revision.
            #
            # Otherwise, the WriterAgent may forget that
            # this is a rejection email and accidentally
            # turn it into a sales/partnership email.

            draft = self.writer.revise(
                previous_draft=draft,
                reviewer_feedback=verdict["feedback"],
                org_profile=org_profile,
                email_type=email_type,
                purpose=purpose,
            )


        else:

            if verbose:

                print(
                    "  [orchestrator] max iterations reached, "
                    "using last draft."
                )


        # --------------------------------------------------
        # 3. Parse final email
        # --------------------------------------------------

        subject, body = parse_subject_body(
            draft
        )


        return {
            "subject": subject,
            "body": body,
            "raw": draft,
        }