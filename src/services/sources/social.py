import os
from firecrawl import FirecrawlApp
from typing import Dict, Any, List


class SocialScraper:
    """Scraper pour réseaux sociaux professionnels"""

    def __init__(self):
        from src.config import config
        try:
            self.firecrawl = FirecrawlApp(api_key=config.FIRECRAWL_API_KEY, version="v2")
            print("Firecrawl v2 enabled for SocialScraper")
        except Exception:
            self.firecrawl = FirecrawlApp(api_key=config.FIRECRAWL_API_KEY)
            print("Firecrawl default version for SocialScraper")

    async def scrape(self, profile) -> Dict[str, Any]:
        """Scrape les profils sur autres réseaux"""

        try:
            results = {}

            # Twitter/X
            twitter = await self._find_twitter(profile)
            if twitter:
                results["twitter"] = twitter

            # Medium
            medium = await self._find_medium(profile)
            if medium:
                results["medium"] = medium

            # GitHub
            github = await self._find_github(profile)
            if github:
                results["github"] = github

            return results

        except Exception as e:
            print(f"Erreur Social scraping: {e}")
            return {}

    async def _find_twitter(self, profile) -> Dict:
        """Recherche profil Twitter"""

        search_query = (
            f"{profile.first_name} {profile.last_name} "
            f"{profile.company} site:twitter.com OR site:x.com"
        )

        try:
            search_url = (
                f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            )

            result = self.firecrawl.scrape_url(
                search_url, formats=["markdown"]
            )

            content = getattr(result, 'markdown', '') if result else ''

            # Extraire URL Twitter
            import re

            twitter_pattern = r"https?://(?:twitter|x)\.com/[\w]+"
            matches = re.findall(twitter_pattern, content)

            if matches:
                return {"url": matches[0], "found": True}

            return None

        except Exception as e:
            return None

    async def _find_medium(self, profile) -> Dict:
        """Recherche profil Medium"""

        search_query = f"{profile.first_name} {profile.last_name} site:medium.com"

        try:
            search_url = (
                f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            )

            result = self.firecrawl.scrape_url(
                search_url, formats=["markdown"]
            )

            content = getattr(result, 'markdown', '') if result else ''

            import re

            medium_pattern = r"https?://medium\.com/@?[\w-]+"
            matches = re.findall(medium_pattern, content)

            if matches:
                return {"url": matches[0], "found": True}

            return None

        except Exception as e:
            return None

    async def _find_github(self, profile) -> Dict:
        """Recherche profil GitHub"""

        search_query = f"{profile.first_name} {profile.last_name} site:github.com"

        try:
            search_url = (
                f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            )

            result = self.firecrawl.scrape_url(
                search_url, formats=["markdown"]
            )

            content = getattr(result, 'markdown', '') if result else ''

            import re

            github_pattern = r"https?://github\.com/[\w-]+"
            matches = re.findall(github_pattern, content)

            if matches:
                return {"url": matches[0], "found": True}

            return None

        except Exception as e:
            return None
