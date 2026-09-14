
# Cold Email Generator using RAG & Multi-Agent Orchestration

Personalized cold email generation powered by Retrieval-Augmented Generation (RAG) and a multi-agent architecture.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Technologies Used](#technologies-used)
- [Project Structure](#project-structure)
- [Installation Steps](#installation-steps)
- [Setup Instructions](#setup-instructions)
- [Environment Variables](#environment-variables)
- [How to Run the Project](#how-to-run-the-project)
- [Example Workflow](#example-workflow)
- [Evaluation](#evaluation)
- [Future Improvements](#future-improvements)
- [Known Issues](#limitations)
- [Team Members](#team-members)
-


## Overview

The **Cold Email Generator** is an AI-powered system that automates the creation of highly personalized cold outreach emails. It combines **Retrieval-Augmented Generation (RAG)** — to ground email content in relevant, factual context (e.g., company info, job postings, portfolio data) — with a CREWAI **multi-agent orchestration** pipeline, where specialized agents handle distinct stages of the email-generation process (research, retrieval, drafting, and refinement).

This approach reduces generic, templated outreach and produces emails tailored to the recipient's context, improving relevance and response rates.

---
## RAG (Retrieval-Augmented Generation)

Before the writer agent drafts anything, the system retrieves verified context about the recipient company (industry, services, trust score, market evaluation) from `rag/company_data.json`, using TF-IDF vectorization and cosine similarity. This grounds every email in real data rather than LLM-invented facts. A minimum relevance threshold (0.15) prevents a weak, coincidental text match from being treated as valid company context.

## Multi-Agent Orchestration (CrewAI)

Each LLM call — drafting, revising, or reviewing — runs as a single-agent, single-task CrewAI `Crew`, routed to Groq's Llama 3.3 70B model via CrewAI's `LLM` class. The writer (temperature 0.7) and reviewer (temperature 0.2) are deliberately tuned differently: fluent generation vs. consistent judgment. The orchestrator loops between them, feeding the reviewer's structured feedback back into the writer's next revision, up to 3 rounds.


## Features

- ✉️ **Personalized Email Generation** — Generates cold emails tailored to specific companies, roles, or prospects.
- 📚 **Document Retrieval (RAG)** — Retrieves relevant context from a knowledge base (e.g., portfolio, past projects, case studies) to ground generated content.
- 🔍 **Vector Search using TF IDF retrival and cosine similarity** — Efficient semantic search over embedded documents.And find the best matching company for the required problem
- 🤖 **Multi-Agent Workflow** — Coordinates multiple agents (e.g., research agent, retrieval agent, writer agent) to collaboratively produce the final email.
- ⚡ **FastAPI Backend** — Exposes the generation pipeline via a lightweight REST API.


---

## System Architecture

```
                ┌─────────────────────┐
                │   User Input         │
                │ (Job/Company Info)   │
                └──────────┬───────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │  Research Agent      │
                │ (extracts context)  │
                └──────────┬───────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │  Retrieval Agent     │
                │ (RAG )               │
                └──────────┬───────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   Writer Agent       │
                │ (drafts the email)  │
                └──────────┬───────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │  Reviewer Agent     │
                │ (tone, formatting)  │
                └──────────┬───────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │  Final Cold Email    │
                └─────────────────────┘
```

Each agent operates independently but shares state through the orchestration layer, allowing modular updates (e.g., swapping the retrieval strategy or LLM provider) without affecting the rest of the pipeline.

---

## Technologies Used

| Category            | Technology     |
|---------------------|----------------|
| Language             | Python |
| Backend Framework    | FastAPI |
| Orchestration        | CREWAI  |
| LLM Provider         |  Groq  |
| Environment Mgmt     | python-dotenv |

---
## Tech Stack

Groq (Llama 3.3 70B) · CrewAI · Tavily · scikit-learn · Streamlit (for frontend) · Python 3.11

## Project Structure

```
cold-email-generator/
├── app.py                  # Main application entry point
├── agents/                 # Multi-agent logic
│   ├── research_agent.py
│   ├── retrieval_agent.py
│   └── writer_agent.py      #orchestration in CREWAI
├── rag/                     # RAG pipeline components
│   ├── embeddings.py
│   └── vector_store.py
├── data/                    # Source documents / knowledge base
├── requirements.txt         # Python dependencies
├── .env.example             # Sample environment variables
|----App.py          
└── README.md
```

---

## Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/shubhangigiri2006-hub/cold_email_generator.git
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Deployed App**
Pip install streamlit
Streamlit run app.py
---

## Setup Instructions

1. Create a `.env` file in the project root (see [Environment Variables](#environment-variables)).
2. Verify API keys for your chosen LLM provider are valid and have sufficient quota.

---

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# LLM Provider API Key
GROQ_LLM_API KEY=your_openai_api_key_here
TAVILIY_API_KEY=tavily_api_key

#
username=admin
password=changme

#SMTP 
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=" "
SMTP_PASSWORD=" "
```

> Replace the values with your own credentials and configuration. Never commit your `.env` file to version control.

---

## How to Run the Project

1. **Start the FastAPI server**
   ```bash
   python app.py
   ```
2.Pip install streamlit
Streamlit run app.py
---

## Example Workflow

**Input:**
```json
{
  "company_name": "Acme Corp",
  "job_description": "Looking for a backend engineer skilled in Python and distributed systems.",
  "sender_profile": "Experienced backend developer with 3+ years in Python and microservices."
}
```

**Pipeline:**
1. The **Research Agent** extracts key details from the job description.
2. The **Retrieval Agent** queries ChromaDB for relevant portfolio projects or case studies.
3. The **Writer Agent** drafts a personalized email combining the retrieved context.
4. The **Reviewer Agent** polishes tone and formatting.

**Output:**
```
Subject: Backend Engineer Ready to Support Acme Corp's Distributed Systems Goals

Hi [Hiring Manager],

I came across Acme Corp's opening for a backend engineer skilled in Python and 
distributed systems, and I believe my experience building scalable microservices 
aligns well with your team's needs...

[Personalized content continues]
```

---

## Evaluation



If evaluation is implemented, consider documenting:
- **Relevance scoring** — How closely generated emails match retrieved context.
- **Human feedback loop** — Manual review/rating of generated emails.
- **A/B testing** — Comparing response rates across different prompt strategies.

---

## Future Improvements

- 🔄 Add feedback loop for continuous learning from sent email performance
- 🌐 Support multiple LLM providers with runtime switching
- 📊 Add analytics dashboard for tracking email performance
- 🧵 Add conversation memory for multi-touch email sequences
- 🖥️ Build a frontend UI for non-technical users

---

## Known Issues / Limitations

- **Web-based email discovery is unreliable.** Search results sometimes surface listicle/aggregator articles ("Top 10 Best...") rather than individual companies, and even real company sites often hide contact emails behind forms or JavaScript rendering that simple scraping can't see. The manual-entry fallback exists specifically because of this.
- **CrewAI + Groq required two workarounds:** (1) a version conflict between CrewAI's and LiteLLM's required `httpx` versions, resolved via controlled reinstallation order; (2) a confirmed CrewAI bug ([issue #5886](https://github.com/crewAIInc/crewAI/issues/5886)) where a prompt-caching field is injected into messages for all providers but only stripped for Anthropic, causing Groq to reject requests — resolved via a documented community monkey-patch.
- **Admin authentication is a placeholder** — plaintext credential comparison against environment variables, not production-grade auth.
- **Single-tenant by design** — configured for one organization profile at a time via `.env`.
- **RAG uses TF-IDF, not semantic embeddings** — matches on keyword overlap rather than meaning; a natural upgrade path is `sentence-transformers` + FAISS/Chroma as the knowledge base scales.
  ```
## Team Members

SHUBHANGI GIRI, ARPIT UPADHYAY, AKSHITA TIWARI , SANJANA, NISHTHA JANGIR



=======
# Cold_Email_Generator-
>>>>>>> fef56cea6f67f35cd2f0ae4707b0eef0e17799a7
