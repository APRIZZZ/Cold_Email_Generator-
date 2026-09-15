from typing import Dict, Optional

from agents.llm_client import complete


WRITER_SYSTEM_PROMPT = """You are an elite B2B email strategist writing on behalf of {org_name}.

Your emails consistently get replies because they feel written by a human who
actually researched the recipient — never like a mail-merge template.

HARD RULES:
- Open with a specific, relevant hook tied to the RECIPIENT CONTEXT (their industry,
  known services, or market position) — never a generic greeting like "I hope this
  email finds you well" or "I came across your company."
- Every specific claim about the recipient must be grounded in the CONTEXT provided.
  Never invent facts, numbers, achievements, or details not given to you.
- If RECIPIENT CONTEXT is sparse or missing, do NOT fabricate specifics — instead,
  write with confident, warm professionalism and let the sender's own value speak,
  rather than faking familiarity with the recipient.
- One sentence should make the recipient feel this email could not have been sent
  to anyone else.
- End with a single, low-friction call to action (e.g. a short call, a quick reply,
  not "let me know your thoughts on everything").
- Tone: formal enough to respect a business relationship, warm enough to feel human,
  confident enough to motivate a response. No corporate jargon, no filler phrases.

The EMAIL TYPE determines the purpose and tone of the email. Follow the
instructions for that email type exactly.

Output format (strict):
SUBJECT: <one line, specific, non-spammy, under 60 characters>
BODY:
<email body, 120-180 words, ending with the appropriate call to action for this email type>
"""


EMAIL_TYPE_INSTRUCTIONS = {

    "request_service": (
        "IMPORTANT: The SENDER is the one who NEEDS a service. "
        "The RECIPIENT is the potential service provider. "
        "Do NOT pitch the sender's own services. "
        "Open by connecting the sender's need to something specific about the "
        "recipient's known expertise or services (from RECIPIENT CONTEXT) — "
        "explain briefly why THIS recipient, specifically, seems like the right fit. "
        "Then state the need clearly and ask whether they can help, with a simple "
        "next step (e.g. a short call)."
    ),

    "provide_service": (
        "IMPORTANT: The SENDER is offering its own services to the RECIPIENT, "
        "who is a potential client. Open by naming something specific about the "
        "recipient (their industry, known services, or market position from "
        "RECIPIENT CONTEXT) and connect it directly to a concrete benefit the "
        "sender's services would bring THEM specifically — not a generic pitch "
        "that could go to any company. Avoid listing every service the sender "
        "offers; pick the one or two most relevant to this recipient."
    ),

    "hire_candidate": (
        "IMPORTANT: This email informs a candidate that they have been selected "
        "or hired. Be warm, genuinely congratulatory, and specific about what "
        "excites the organization about them joining (if details are given). "
        "Clearly explain any next steps. Make the candidate feel welcomed, not "
        "processed."
    ),

    "reject_candidate": (
        "IMPORTANT: This is a candidate rejection email.\n"
        "The RECIPIENT is an individual candidate, NOT a company.\n"
        "Clearly and respectfully inform the candidate that they were not selected "
        "for the position they applied for.\n"
        "Thank them genuinely for their time and interest in the organization.\n"
        "Be professional, respectful, and encouraging without being falsely hopeful.\n"
        "Do NOT pitch any services.\n"
        "Do NOT write a partnership proposal.\n"
        "Do NOT describe the candidate as a company.\n"
        "Do NOT say that you researched the candidate's company.\n"
        "Do NOT invent achievements, qualifications, interview performance, "
        "or reasons for rejection.\n"
        "If no specific reason is provided, simply state that another candidate "
        "was selected or that the decision was based on the requirements of the role.\n"
        "Address the candidate personally by their name when available."
    ),

    "notification": (
        "IMPORTANT: This is a broadcast announcement, not a personalized sales "
        "pitch or service request. Keep it informative, clear, and appropriately "
        "toned for the announcement — but still avoid sounding robotic or templated."
    ),
}


def _format_company_context(
    company_context: Optional[Dict]
) -> str:

    if not company_context:
        return "No specific data available about the recipient."

    lines = [
        f"Recipient: {company_context.get('company_name', 'Unknown')}"
    ]

    if company_context.get("industry"):
        lines.append(
            f"Industry: {company_context['industry']}"
        )

    if company_context.get("services"):

        services = company_context["services"]

        if isinstance(services, list):
            services = ", ".join(services)

        lines.append(
            f"Known services: {services}"
        )

    if company_context.get("trust_score") is not None:
        lines.append(
            f"Market trust score (0-10): "
            f"{company_context['trust_score']}"
        )

    if company_context.get("market_evaluation"):
        lines.append(
            f"Market evaluation: "
            f"{company_context['market_evaluation']}"
        )

    return "\n".join(lines)


class WriterAgent:

    def draft(
        self,
        purpose: str,
        org_profile: Dict,
        company_context: Optional[Dict] = None,
        email_type: str = "request_service",
    ) -> str:

        system = WRITER_SYSTEM_PROMPT.format(
            org_name=org_profile.get(
                "name",
                "our organization"
            )
        )

        type_instruction = EMAIL_TYPE_INSTRUCTIONS.get(
            email_type,
            ""
        )

        user_prompt = f"""
EMAIL TYPE:
{email_type}

EMAIL-TYPE-SPECIFIC INSTRUCTIONS:
{type_instruction}

PURPOSE / INTENT FROM ADMIN:
{purpose}

SENDER ORGANIZATION PROFILE:
Name: {org_profile.get('name')}
Website: {org_profile.get('website')}
Services offered: {org_profile.get('services')}
Description: {org_profile.get('description')}
Sender: {org_profile.get('sender_name')}
Sender title: {org_profile.get('sender_title')}

RECIPIENT CONTEXT:
{_format_company_context(company_context)}

Write the email now. Make the opening line impossible to mistake for a template.

Follow the required SUBJECT/BODY format exactly.
"""

        return complete(
            system,
            user_prompt,
            max_tokens=600,
            temperature=0.7,
        )


    def revise(
        self,
        previous_draft: str,
        reviewer_feedback: str,
        org_profile: Dict,
        email_type: str = "request_service",
        purpose: str = "",
    ) -> str:

        system = WRITER_SYSTEM_PROMPT.format(
            org_name=org_profile.get(
                "name",
                "our organization"
            )
        )

        type_instruction = EMAIL_TYPE_INSTRUCTIONS.get(
            email_type,
            ""
        )

        user_prompt = f"""
EMAIL TYPE:
{email_type}

EMAIL-TYPE-SPECIFIC INSTRUCTIONS:
{type_instruction}

ORIGINAL PURPOSE:
{purpose}

PREVIOUS EMAIL DRAFT:
---
{previous_draft}
---

REVIEWER FEEDBACK:
---
{reviewer_feedback}
---

Revise the email to address the reviewer's feedback.

IMPORTANT:
Preserve the original email type and purpose.
Do not transform the email into a different type.

For example, a reject_candidate email must remain a candidate rejection email.
It must not become a sales pitch, partnership email, or generic business email.

Keep the required SUBJECT/BODY format.
"""

        return complete(
            system,
            user_prompt,
            max_tokens=600,
            temperature=0.7,
        )