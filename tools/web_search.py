import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

from config import TAVILY_API_KEY

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

PREFERRED_PREFIXES = ["sales", "partnerships", "business", "contact", "hello", "info", "bd"]


class WebSearchTool:
    def __init__(self):
        self.use_tavily = bool(TAVILY_API_KEY)
        if self.use_tavily:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=TAVILY_API_KEY)
            except ImportError:
                self.use_tavily = False

    # 1. Find companies matching a service request
    def search_companies_for_service(self, query: str, max_results: int = 5) -> List[Dict]:
        search_query = f"companies that provide {query}"
        if self.use_tavily:
            return self._tavily_search(search_query, max_results)
        return self._duckduckgo_search(search_query, max_results)

    def _tavily_search(self, query: str, max_results: int) -> List[Dict]:
        response = self._client.search(query=query, max_results=max_results)
        results = []
        for r in response.get("results", []):
            results.append({
                "name": r.get("title", "Unknown"),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
            })
        return results

    def _duckduckgo_search(self, query: str, max_results: int) -> List[Dict]:
        try:
            resp = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            soup = BeautifulSoup(resp.text, "html.parser")
            results = []
            for result in soup.select(".result")[:max_results]:
                title_tag = result.select_one(".result__title a")
                snippet_tag = result.select_one(".result__snippet")
                if not title_tag:
                    continue
                results.append({
                    "name": title_tag.get_text(strip=True),
                    "url": title_tag.get("href", ""),
                    "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
                })
            return results
        except requests.RequestException:
            return []

    # 2. Find a contact email for a specific company
    def find_company_email(self, company_name: str, website: Optional[str] = None) -> Optional[str]:
        candidate_emails: List[str] = []

        if not website:
            hits = self.search_companies_for_service(f'"{company_name}" official website')
            if hits:
                website = hits[0]["url"]

        if website:
            candidate_emails += self._scrape_emails_from_url(website)
            for path in ("/contact", "/contact-us", "/about"):
                candidate_emails += self._scrape_emails_from_url(website.rstrip("/") + path)

        if not candidate_emails:
            hits = self.search_companies_for_service(f"{company_name} contact email", max_results=3)
            for h in hits:
                candidate_emails += EMAIL_REGEX.findall(h.get("snippet", ""))

        return self._pick_best_email(candidate_emails)

    def _scrape_emails_from_url(self, url: str) -> List[str]:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            return EMAIL_REGEX.findall(resp.text)
        except requests.RequestException:
            return []

    def _pick_best_email(self, emails: List[str]) -> Optional[str]:
        if not emails:
            return None
        emails = list(dict.fromkeys(emails))
        for prefix in PREFERRED_PREFIXES:
            for e in emails:
                if e.lower().startswith(prefix):
                    return e
        return emails[0]