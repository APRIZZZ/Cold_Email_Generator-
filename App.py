
import os
import streamlit as st

# Load Streamlit secrets into os.environ so existing os.getenv() calls keep working
if hasattr(st, "secrets"):
    for key, value in st.secrets.items():
        os.environ[key] = str(value)
from config import ADMIN_USERNAME, ADMIN_PASSWORD, ORG_PROFILE
from rag.company_knowledge_base import CompanyKnowledgeBase
from tools.web_search import WebSearchTool
from tools import email_utils
from agents.orchestrator import EmailOrchestrator
from workflows.request_service import _clean_search_query as _clean_search_query_request
from workflows.provide_service import _clean_search_query as _clean_search_query_provide


st.set_page_config(page_title="Cold Email Generator", layout="centered")



@st.cache_resource
def get_context():
    return {
        "org_profile": ORG_PROFILE,
        "rag_kb": CompanyKnowledgeBase(),
        "web_search": WebSearchTool(),
        "orchestrator": EmailOrchestrator(),
    }


MENU_OPTIONS = [
    {"key": "request_service", "label": "Request a service",
     "description": "Ask a company to provide you with a service."},
    {"key": "provide_service", "label": "Provide a service",
     "description": "Pitch a service you offer to a prospective company."},
    {"key": "hire_candidate", "label": "Hire a candidate",
     "description": "Send an offer email to a candidate."},
    {"key": "reject_candidate", "label": "Reject a candidate",
     "description": "Send a respectful rejection email to a candidate."},
    {"key": "send_notification", "label": "Send a notification",
     "description": "Send a notification to one or more recipients."},
]



def sget(page: str, name: str, default=None):
    return st.session_state.setdefault(f"{page}__{name}", default)


def sset(page: str, name: str, value):
    st.session_state[f"{page}__{name}"] = value


def sclear(page: str):
    prefix = f"{page}__"
    for k in [k for k in st.session_state.keys() if k.startswith(prefix)]:
        del st.session_state[k]


def go_to_menu():
    st.session_state.page = "menu"


def open_page(page: str):
    st.session_state.page = page
    sclear(page)  # fresh start whenever entering a page from the menu


# Login 

def login_screen():
    st.title("Admin Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if submitted:
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid credentials.")


st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("page", "menu")

if not st.session_state.authenticated:
    login_screen()
    st.stop()


ctx = get_context()

with st.sidebar:
    st.success("Logged in as admin")
    if st.session_state.page != "menu":
        if st.button("Back to main menu"):
            go_to_menu()
            st.rerun()
        if st.button("Start over"):
            sclear(st.session_state.page)
            st.rerun()
    if st.button("Log out"):
        st.session_state.authenticated = False
        go_to_menu()
        st.rerun()



# review the generated email, edit, and send

def render_review_and_send(page: str, recipients: list):
    """recipients: list of email strings (length 1 for single-target flows)."""
    result = sget(page, "result")

    st.subheader("Generated email")
    subject = st.text_input("Subject", value=result["subject"], key=f"{page}__subject_field")
    body = st.text_area("Body", value=result["body"], height=300, key=f"{page}__body_field")

    if len(recipients) == 1:
        st.write(f"**To:** {recipients[0]}")
    else:
        st.write(f"**To ({len(recipients)} recipients):** {', '.join(recipients)}")

    col1, col2 = st.columns(2)
    if col1.button("Send email", type="primary", key=f"{page}__send_btn"):
        with st.spinner("Sending..."):
            statuses = []
            for r in recipients:
                ok = email_utils.send_email(r, subject, body)
                statuses.append((r, ok))
        for r, ok in statuses:
            if ok:
                st.success(f"Sent to {r}")
            else:
                st.warning(f"Could not confirm send to {r} (printed/logged locally, check email_utils).")
    if col2.button("Discard / start over", key=f"{page}__discard_btn"):
        sclear(page)
        st.rerun()


# resolve an email for a company 

def render_resolve_email(page: str, company_name: str, website, allow_retry: bool):
    web_search = ctx["web_search"]
    st.subheader(f"Finding a contact email for '{company_name}'")

    if sget(page, "auto_checked") is None:
        with st.spinner("Looking up a contact email..."):
            found = web_search.find_company_email(company_name, website)
        sset(page, "auto_checked", True)
        sset(page, "auto_found_email", found)

    found = sget(page, "auto_found_email")

    if found:
        st.success(f"Found email: {found}")
        cols = st.columns(2) if allow_retry else [st]
        if cols[0].button("Use this email", type="primary", key=f"{page}__use_found"):
            sset(page, "target_email", found)
            sset(page, "step", "generate")
            st.rerun()
        if allow_retry and cols[1].button("Enter a different one", key=f"{page}__reject_found"):
            sset(page, "auto_found_email", None)
            st.rerun()
    else:
        st.warning(f"Could not auto-discover an email for '{company_name}'.")
        manual = st.text_input("Enter one manually (leave blank to skip)", key=f"{page}__manual_email")

        cols = st.columns(2) if allow_retry else [st]
        if cols[0].button("Use this email", type="primary", key=f"{page}__use_manual"):
            if manual and email_utils.is_valid_email(manual):
                sset(page, "target_email", manual)
                sset(page, "step", "generate")
                st.rerun()
            elif manual:
                st.error("That doesn't look like a valid email.")
            else:
                st.warning("Enter an email, or pick a different candidate below.")

        if allow_retry and cols[1].button("Try a different candidate", key=f"{page}__try_diff"):
            excluded = sget(page, "excluded", [])
            chosen = sget(page, "chosen_candidate")
            if chosen:
                excluded.append(chosen)
            sset(page, "excluded", excluded)
            sset(page, "chosen_candidate", None)
            sset(page, "auto_checked", None)
            sset(page, "auto_found_email", None)
            sset(page, "step", "search_web")
            st.rerun()


# (find a target company/email, then generate + send)
def render_company_target_flow(page: str, purpose_label: str, email_type: str, clean_query_fn):
    step = sget(page, "step", "input")

    # ---- Step: purpose + how to find the target -----------------------
    if step == "input":
        st.subheader("1. Describe the purpose")
        purpose = st.text_area(purpose_label, value=sget(page, "purpose", ""))

        st.subheader("2. Target company")
        choice_label = st.radio(
            "How do you want to specify the recipient?",
            [
                "Yes, I'll specify the company",
                "No, search the web for a suitable company",
                "I already have the recipient's email address",
            ],
        )
        sub_choice = {"Yes, I'll specify the company": "1",
                       "No, search the web for a suitable company": "2",
                       "I already have the recipient's email address": "3"}[choice_label]

        company_name_manual, manual_email = None, None
        if sub_choice == "1":
            company_name_manual = st.text_input("Company name")
        elif sub_choice == "3":
            company_name_manual = st.text_input("Company name (optional, for context)")
            manual_email = st.text_input("Recipient's email address")

        if st.button("Continue", type="primary"):
            if not purpose.strip():
                st.warning("Purpose cannot be empty.")
            elif sub_choice == "1" and not (company_name_manual or "").strip():
                st.warning("Please enter a company name.")
            elif sub_choice == "3":
                if not (manual_email or "").strip() or not email_utils.is_valid_email(manual_email.strip()):
                    st.warning("Please enter a valid email address.")
                else:
                    sset(page, "purpose", purpose.strip())
                    sset(page, "sub_choice", "3")
                    sset(page, "company_name", (company_name_manual or "the recipient").strip() or "the recipient")
                    sset(page, "target_email", manual_email.strip())
                    sset(page, "step", "generate")
                    st.rerun()
            else:
                sset(page, "purpose", purpose.strip())
                sset(page, "sub_choice", sub_choice)
                if sub_choice == "1":
                    sset(page, "company_name", company_name_manual.strip())
                    sset(page, "chosen_candidate", None)
                    sset(page, "step", "resolve_email")
                else:
                    sset(page, "step", "search_web")
                st.rerun()

    #   web search for a candidate company 
    elif step == "search_web":
        st.subheader("Searching the web for a suitable company")

        if sget(page, "candidates") is None:
            with st.spinner("Building search query and searching..."):
                query = clean_query_fn(sget(page, "purpose"))
                candidates = ctx["web_search"].search_companies_for_service(query)
            sset(page, "candidates", candidates or [])

        excluded = sget(page, "excluded", [])
        remaining = [c for c in sget(page, "candidates") if c not in excluded]

        if not remaining:
            st.error("No candidates found (or all were exhausted). Returning to start.")
            if st.button("Back to start"):
                sclear(page)
                st.rerun()
        else:
            options = [f"{c['name']} ({c['url']})" for c in remaining]
            picked = st.radio("Candidates found:", options)
            picked_candidate = remaining[options.index(picked)]

            if st.button("Select this company", type="primary"):
                sset(page, "chosen_candidate", picked_candidate)
                sset(page, "company_name", picked_candidate["name"])
                sset(page, "auto_checked", None)
                sset(page, "auto_found_email", None)
                sset(page, "step", "resolve_email")
                st.rerun()

    #  resolve an email for the chosen/entered company 
    elif step == "resolve_email":
        company_name = sget(page, "company_name")
        chosen = sget(page, "chosen_candidate")
        website = chosen["url"] if chosen else None
        render_resolve_email(page, company_name, website, allow_retry=(sget(page, "sub_choice") == "2"))

    # generate the email 
    elif step == "generate":
        st.subheader("Ready to generate")
        st.write(f"**To:** {sget(page, 'target_email')}")
        st.write(f"**Company:** {sget(page, 'company_name')}")
        st.write(f"**Purpose:** {sget(page, 'purpose')}")

        if st.button("Generate email", type="primary"):
            with st.spinner("Retrieving company context and drafting with writer/reviewer agents..."):
                rag_kb = ctx["rag_kb"]
                company_name = sget(page, "company_name")
                company_context = rag_kb.find_by_name(company_name) or {"company_name": company_name}
                result = ctx["orchestrator"].generate_email(
                    purpose=sget(page, "purpose"),
                    org_profile=ctx["org_profile"],
                    company_context=company_context,
                    email_type=email_type,
                )
            sset(page, "result", result)
            sset(page, "step", "result")
            st.rerun()

    #  review + send 
    elif step == "result":
        render_review_and_send(page, [sget(page, "target_email")])



def render_candidate_flow(page: str, title: str, purpose_builder, email_type: str):
    step = sget(page, "step", "form")

    if step == "form":
        st.subheader(title)
        candidate_name = st.text_input("Candidate name", value=sget(page, "candidate_name", ""))
        candidate_email = st.text_input("Candidate email", value=sget(page, "candidate_email", ""))
        position = st.text_input("Position", value=sget(page, "position", ""))
        extra = st.text_area(
            "Extra details / notes (optional)",
            value=sget(page, "extra", ""),
            help="Salary, start date, next steps, or reason/feedback, depending on the email type.",
        )

        if st.button("Continue", type="primary"):
            if not candidate_name.strip():
                st.warning("Candidate name cannot be empty.")
            elif not email_utils.is_valid_email(candidate_email.strip()):
                st.warning("That doesn't look like a valid email address.")
            else:
                sset(page, "candidate_name", candidate_name.strip())
                sset(page, "candidate_email", candidate_email.strip())
                sset(page, "position", position.strip())
                sset(page, "extra", extra.strip())
                sset(page, "step", "generate")
                st.rerun()

    elif step == "generate":
        st.subheader("Ready to generate")
        st.write(f"**To:** {sget(page, 'candidate_email')}")
        st.write(f"**Candidate:** {sget(page, 'candidate_name')}")
        st.write(f"**Position:** {sget(page, 'position')}")

        if st.button("Generate email", type="primary"):
            purpose = purpose_builder(
                sget(page, "candidate_name"), sget(page, "position"), sget(page, "extra")
            )
            with st.spinner("Drafting with writer/reviewer agents..."):
                result = ctx["orchestrator"].generate_email(
                    purpose=purpose,
                    org_profile=ctx["org_profile"],
                    company_context={"company_name": sget(page, "candidate_name")},
                    email_type=email_type,
                )
            sset(page, "result", result)
            sset(page, "step", "result")
            st.rerun()

    elif step == "result":
        render_review_and_send(page, [sget(page, "candidate_email")])


def hire_purpose(name, position, extra):
    return (
        f"Inform {name} they have been selected/hired for the position "
        f"of {position}. Additional details: {extra or 'none provided'}."
    )


def reject_purpose(name, position, extra):
    return (
        f"Politely inform {name} that they were not selected for the "
        f"position of {position}. Keep it respectful and encouraging. "
        f"Note: {extra or 'no specific reason to share'}."
    )


# notification.py — multi-recipient flow

def render_notification_flow(page: str):
    step = sget(page, "step", "form")

    if step == "form":
        st.subheader("Send a notification")
        notif_type = st.text_input(
            "What kind of notification is this?",
            value=sget(page, "notif_type", ""),
            placeholder="e.g. new position opened, sale/promotion, general announcement",
        )
        details = st.text_area("Details", value=sget(page, "details", ""))
        recipients_raw = st.text_area(
            "Recipient email(s), comma-separated", value=sget(page, "recipients_raw", "")
        )

        if st.button("Continue", type="primary"):
            if not notif_type.strip():
                st.warning("Notification type cannot be empty.")
            else:
                recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
                valid = [r for r in recipients if email_utils.is_valid_email(r)]
                invalid = [r for r in recipients if r not in valid]
                if invalid:
                    st.warning(f"Ignoring invalid email(s): {', '.join(invalid)}")
                if not valid:
                    st.warning("No valid recipient emails provided.")
                else:
                    sset(page, "notif_type", notif_type.strip())
                    sset(page, "details", details.strip())
                    sset(page, "recipients_raw", recipients_raw)
                    sset(page, "recipients", valid)
                    sset(page, "step", "generate")
                    st.rerun()

    elif step == "generate":
        recipients = sget(page, "recipients")
        st.subheader("Ready to generate")
        st.write(f"**To ({len(recipients)}):** {', '.join(recipients)}")
        st.write(f"**Type:** {sget(page, 'notif_type')}")

        if st.button("Generate email", type="primary"):
            purpose = f"Notification type: {sget(page, 'notif_type')}. Details: {sget(page, 'details')}"
            with st.spinner("Drafting with writer/reviewer agents..."):
                result = ctx["orchestrator"].generate_email(
                    purpose=purpose,
                    org_profile=ctx["org_profile"],
                    company_context=None,
                    email_type="notification",
                )
            sset(page, "result", result)
            sset(page, "step", "result")
            st.rerun()

    elif step == "result":
        render_review_and_send(page, sget(page, "recipients"))


# Main menu

def render_menu():
    st.title("Cold Email Generator")
    st.caption("Main menu — choose what you'd like to do")
    st.write("")

    for opt in MENU_OPTIONS:
        with st.container(border=True):
            col_text, col_action = st.columns([7, 3])
            with col_text:
                st.markdown(f"**{opt['label']}**")
                st.caption(opt["description"])
            with col_action:
                st.write("")
                if st.button("Open", key=f"open_{opt['key']}", type="primary", use_container_width=True):
                    open_page(opt["key"])
                    st.rerun()

    st.write("")
   



# Router

page = st.session_state.page

if page == "menu":
    render_menu()
elif page == "request_service":
    st.title("Request a Service")
    render_company_target_flow(
        page, "Describe the service you require (one line)", "request_service", _clean_search_query_request
    )
elif page == "provide_service":
    st.title("Provide a Service")
    render_company_target_flow(
        page,
        "Describe the service you want to pitch, and to what kind of company (one line)",
        "provide_service",
        _clean_search_query_provide,
    )
elif page == "hire_candidate":
    st.title("Hire a Candidate")
    render_candidate_flow(page, "Candidate details", hire_purpose, "hire_candidate")
elif page == "reject_candidate":
    st.title("Reject a Candidate")
    render_candidate_flow(page, "Candidate details", reject_purpose, "reject_candidate")
elif page == "send_notification":
    st.title("Send a Notification")
    render_notification_flow(page)