import json
import os
import re
from typing import List, Dict, Any
from task_2_email_triage.schemas import KnowledgeArticle


class KnowledgeRetriever:
    """Retrieves relevant support documentation based on email content and intent."""

    def __init__(self, docs_path: str = None):
        if not docs_path:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            docs_path = os.path.join(current_dir, "docs.json")

        self.docs_path = docs_path
        self.articles: List[KnowledgeArticle] = self._load_docs()

    def _load_docs(self) -> List[KnowledgeArticle]:
        if not os.path.exists(self.docs_path):
            return []
        with open(self.docs_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            return [KnowledgeArticle(**item) for item in raw]

    def search(self, query: str, top_k: int = 2) -> List[KnowledgeArticle]:
        """Performs token-based relevance scoring over knowledge base articles."""
        if not self.articles:
            return []

        tokens = set(re.findall(r"\w+", query.lower()))
        scored_articles = []

        for article in self.articles:
            score = 0
            # Match keywords
            for kw in article.keywords:
                if kw in query.lower():
                    score += 3

            # Match title
            title_tokens = set(re.findall(r"\w+", article.title.lower()))
            score += len(tokens.intersection(title_tokens)) * 2

            # Match content
            content_tokens = set(re.findall(r"\w+", article.content.lower()))
            score += len(tokens.intersection(content_tokens))

            scored_articles.append((score, article))

        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [article for score, article in scored_articles[:top_k] if score > 0] or self.articles[:1]

    def get_context_summary(self, query: str) -> str:
        """Returns formatted string of relevant documentation for LLM prompt context."""
        matched = self.search(query)
        if not matched:
            return "No specific internal documentation found."
        
        snippets = []
        for doc in matched:
            snippets.append(f"[{doc.id}: {doc.title}]\n{doc.content}")
        return "\n\n".join(snippets)
