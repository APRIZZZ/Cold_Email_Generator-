import json
import os
from typing import List, Dict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_PATH = os.path.join(os.path.dirname(__file__), "company_data.json")


def _company_to_document(company: Dict) -> str:
    """Flatten a company record into one text blob so we can search it."""
    return " ".join([
        company.get("company_name", ""),
        company.get("industry", ""),
        " ".join(company.get("services", [])),
        company.get("market_evaluation", ""),
    ])


class CompanyKnowledgeBase:
    def __init__(self, data_path: str = DATA_PATH):
        with open(data_path, "r", encoding="utf-8") as f:
            self.companies: List[Dict] = json.load(f)

        self._documents = [_company_to_document(c) for c in self.companies]
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(self._documents)

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        if not query.strip():
            return []
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix).flatten()
        ranked_idx = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in ranked_idx:
            if scores[idx] <= 0:
                continue
            record = dict(self.companies[idx])
            record["relevance_score"] = round(float(scores[idx]), 4)
            results.append(record)
        return results

    def find_by_name(self, company_name: str) -> Dict:
        name_lower = company_name.strip().lower()
        for c in self.companies:
            if c["company_name"].strip().lower() == name_lower:
                return dict(c)
        hits = self.retrieve(company_name, top_k=1)
        return hits[0] if hits else {}

    def add_company(self, company: Dict):
        """Grows the knowledge base at runtime -- this is how we'll plug
        in newly-discovered companies from web search later."""
        self.companies.append(company)
        self._documents.append(_company_to_document(company))
        self._matrix = self._vectorizer.fit_transform(self._documents)