import os
from firecrawl import FirecrawlApp
from typing import Dict, Any, List
import asyncio


class NewsScraper:
    """Scraper pour articles de presse et mentions médias"""

    def __init__(self):
        try:
            self.firecrawl = FirecrawlApp(api_key="fc-56bf239c38ed4a1b820ffa50eb758eae", version="v2")
            print("Firecrawl v2 enabled for NewsScraper")
        except Exception:
            self.firecrawl = FirecrawlApp(api_key="fc-56bf239c38ed4a1b820ffa50eb758eae")
            print("Firecrawl default version for NewsScraper")

    async def scrape(self, profile) -> Dict[str, Any]:
        """Scrape les articles de presse mentionnant la personne"""

        try:
            # Recherche Google News
            articles = await self._search_news_articles(profile)

            # Recherche mentions sur médias pro (Les Échos, etc.)
            pro_mentions = await self._search_professional_media(profile)

            return {
                "news_articles": articles,
                "professional_mentions": pro_mentions,
                "total_mentions": len(articles) + len(pro_mentions),
            }

        except Exception as e:
            print(f"Erreur News scraping: {e}")
            return {"error": str(e)}

    async def _search_news_articles(self, profile) -> List[Dict]:
        """Recherche d'articles de presse"""
        try:
            search_query = (
                f"{profile.first_name} {profile.last_name} " f"{profile.company}"
            )
            search_url = (
                f"https://www.google.com/search?q={search_query.replace(' ', '+')}" 
                f"&tbm=nws"
            )

            result = self.firecrawl.scrape_url(
                search_url, params={"formats": ["markdown"]}
            )

            content = result.get("markdown", "")

            # Parser les résultats (simplifiés)
            articles = self._parse_news_results(content)

            return articles[:5]  # Max 5 articles
        except Exception as e:
            print(f"Erreur recherche news: {e}")
            return []

    async def _search_professional_media(self, profile) -> List[Dict]:
        """Recherche sur médias professionnels français"""

        pro_media = ["lesechos.fr", "challenges.fr", "usinenouvelle.com"]

        mentions = []

        for media in pro_media:
            try:
                search_query = (
                    f"site:{media} " f"{profile.first_name} {profile.last_name}"
                )

                search_url = (
                    f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
                )

                result = self.firecrawl.scrape_url(
                    search_url, params={"formats": ["markdown"]}
                )

                # Parser et ajouter aux mentions
                content = result.get("markdown", "")

                if profile.last_name.lower() in content.lower():
                    mentions.append(
                        {"source": media, "found": True, "snippet": content[:200]}
                    )

            except Exception as e:
                continue

        return mentions

    def _parse_news_results(self, markdown: str) -> List[Dict]:
        """Parse les résultats de recherche news"""

        articles = []

        # Split par lignes et chercher des patterns d'articles
        lines = markdown.split("\n")

        current_article = {}

        for line in lines:
            line = line.strip()

            # Détecter un titre (commence souvent par #)
            if line.startswith("#") and len(line) > 10:
                if current_article:
                    articles.append(current_article)
                current_article = {"title": line.replace("#", "").strip()}

            # Détecter une URL
            elif "http" in line and current_article:
                import re

                urls = re.findall(r"https?://[^\s]+", line)
                if urls:
                    current_article["url"] = urls[0]

            # Détecter un snippet
            elif (
                len(line) > 50 and current_article and "snippet" not in current_article
            ):
                current_article["snippet"] = line

        if current_article:
            articles.append(current_article)

        return articles
