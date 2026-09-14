from typing import Dict, Optional
from agents.llm_client import complete

REVIEWER_SYSTEM_PROMPT = """You are a meticulous email quality reviewer for B2B cold emails.
Check the draft against these criteria:
1. Professional tone, no generic filler ("I hope this email finds you well" is banned).
2. Every specific claim about the recipient company is grounded in the given CONTEXT
   (flag anything that looks invented/hallucinated).
3. Subject line is specific and non-spammy.
4. Body is 120-180 words with one clear call to action.
5. No grammar issues.

Output format (strict):
VERDICT: APPROVE or REVISE
FEEDBACK: <if REVISE, concrete actionable feedback the writer should apply. If APPROVE, write "None">
"""


class ReviewerAgent:
    def review(self, draft: str, company_context: Optional[Dict] = None) -> Dict:
        context_str = str(company_context) if company_context else "No specific company data available."
        user_prompt = f"""
DRAFT EMAIL:
---
{draft}
---

RECIPIENT CONTEXT USED FOR GROUNDING:
{context_str}

Evaluate the draft now.
"""
        result = complete(REVIEWER_SYSTEM_PROMPT, user_prompt, max_tokens=400, temperature=0.2)

        verdict = "REVISE"
        feedback = result
        for line in result.splitlines():
            if line.strip().upper().startswith("VERDICT:"):
                verdict = line.split(":", 1)[1].strip().upper()
            if line.strip().upper().startswith("FEEDBACK:"):
                feedback = line.split(":", 1)[1].strip()

        return {"approved": verdict.startswith("APPROVE"), "feedback": feedback}