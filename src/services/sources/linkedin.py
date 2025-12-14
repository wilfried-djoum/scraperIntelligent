"""
services/sources/linkedin.py
Scraper pour LinkedIn utilisant Firecrawl
"""

import os
import re
from typing import Dict, Any, List, Optional
from firecrawl import FirecrawlApp
import asyncio
import certifi


class LinkedInScraper:
    """Scraper pour profils LinkedIn via Firecrawl"""

    def __init__(self):
        # Force trusted CA bundle to avoid invalid REQUESTS_CA_BUNDLE/SSL issues
        try:
            os.environ.setdefault("SSL_CERT_FILE", certifi.where())
            os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
        except Exception:
            pass
        api_key = "fc-56bf239c38ed4a1b820ffa50eb758eae"
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY non trouvée dans .env")

        # Prefer Firecrawl v2 if available in client
        try:
            self.firecrawl = FirecrawlApp(api_key=api_key, version="v2")
            print("Firecrawl client initialized with v2")
        except Exception:
            self.firecrawl = FirecrawlApp(api_key=api_key)
            print("Firecrawl client initialized with default version")
        self.last_debug: Dict[str, Any] = {}
        print("LinkedInScraper initialisé")

    async def scrape(self, profile) -> Dict[str, Any]:
        """
        Scrape le profil LinkedIn complet

        Args:
            profile: BaseProfile avec first_name, last_name, company

        Returns:
            Dict contenant profile, posts, comments, url
        """
        print(f"\nScraping LinkedIn pour {profile.getFullName()}...")

        try:
            # Étape 1: Trouver l'URL du profil LinkedIn (candidats puis recherche)
            linkedin_url = await self._find_linkedin_profile(profile)

            if not linkedin_url:
                print("Profil LinkedIn non trouvé")
                return {
                    "error": "Profil LinkedIn non trouvé",
                    "profile": {},
                    "posts": [],
                    "comments": [],
                    "url": None,
                }

            print(f"Profil trouvé: {linkedin_url}")

            # Étape 2: Scraper le profil principal
            profile_data = await self._scrape_profile_page(linkedin_url)

            # Étape 3: Scraper les posts récents (simplifié pour l'instant)
            posts = await self._scrape_recent_posts(linkedin_url)

            # Étape 4: Commentaires (à implémenter plus tard)
            comments = []  # Optionnel pour la v1

            return {
                "profile": profile_data,
                "posts": posts[:10],  # Maximum 10 posts
                "comments": comments,
                "url": linkedin_url,
            }

        except Exception as e:
            print(f"Erreur LinkedIn scraping: {e}")
            import traceback

            traceback.print_exc()
            return {
                "error": str(e),
                "profile": {},
                "posts": [],
                "comments": [],
                "url": None,
            }

    async def _find_linkedin_profile(self, profile) -> Optional[str]:
        """
        Trouve l'URL du profil LinkedIn via recherche Google

        Returns:
            URL du profil LinkedIn ou None
        """
        # 1) Générer des URLs candidates déterministes
        candidates = self._build_linkedin_candidates(profile)
        print(f"Candidats LinkedIn: {candidates}")
        self.last_debug = {
            "candidates": candidates,
            "validated": None,
            "search_google_used": False,
            "search_linkedin_used": False,
        }
        for url in candidates:
            if await self._validate_profile_url(url):
                print(f"URL candidate valide: {url}")
            self.last_debug["validated"] = url
            return url

        # 2) Fallback: Recherche Google avec filtre site
        search_query = (
            f"{profile.first_name} {profile.last_name} "
            f"{getattr(profile, 'company', '')} site:linkedin.com/in/"
        )
        print(f"Recherche Google: {search_query}")
        try:
            search_url = (
                f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            )
            result = self.firecrawl.scrape_url(
                search_url, params={"formats": ["markdown"], "onlyMainContent": False}
            )
            print(
                "[Firecrawl RAW Search]",
                {
                    "url": search_url,
                    "has_markdown": bool(result and result.get("markdown")),
                    "markdown_len": len(result.get("markdown", "")) if result else 0,
                    "keys": list(result.keys()) if isinstance(result, dict) else None,
                },
            )
            if not result or "markdown" not in result:
                print("Aucun résultat de recherche")
                # 3) Fallback: Recherche directe LinkedIn
                self.last_debug["search_google_used"] = True
                found = await self._linkedin_search_fallback(profile)
                if found:
                    self.last_debug["search_linkedin_used"] = True
                return found
            content = result.get("markdown", "")
            linkedin_pattern = r"https?://(?:www\.)?linkedin\.com/in/[\w\-]+"
            matches = re.findall(linkedin_pattern, content)
            if matches:
                linkedin_url = matches[0]
                print(f"URL trouvée: {linkedin_url}")
                self.last_debug["search_google_used"] = True
                return linkedin_url
            print("Aucune URL LinkedIn trouvée dans les résultats")
            # 3) Fallback: Recherche directe LinkedIn
            self.last_debug["search_google_used"] = True
            found = await self._linkedin_search_fallback(profile)
            if found:
                self.last_debug["search_linkedin_used"] = True
            return found
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            # 3) Fallback: Recherche directe LinkedIn
            found = await self._linkedin_search_fallback(profile)
            if found:
                self.last_debug["search_linkedin_used"] = True
            return found

    async def _linkedin_search_fallback(self, profile) -> Optional[str]:
        """Effectue une recherche directement sur LinkedIn et extrait des URLs /in/"""
        import urllib.parse

        keywords = f"{profile.first_name} {profile.last_name} {getattr(profile, 'company', '')}".strip()
        q = urllib.parse.quote(keywords)
        url = f"https://www.linkedin.com/search/results/all/?keywords={q}&origin=GLOBAL_SEARCH_HEADER"
        print(f"Recherche LinkedIn directe: {url}")
        try:
            result = self.firecrawl.scrape_url(
                url,
                params={
                    "formats": ["markdown", "html"],
                    "onlyMainContent": False,
                    "waitFor": 3000,
                },
            )
            print(
                "[Firecrawl RAW LinkedIn Search]",
                {
                    "url": url,
                    "has_markdown": bool(result and result.get("markdown")),
                    "markdown_len": len(result.get("markdown", "")) if result else 0,
                    "has_html": bool(result and result.get("html")),
                    "html_len": len(result.get("html", "")) if result else 0,
                },
            )
            content = (
                (result or {}).get("markdown", "")
                + "\n"
                + (result or {}).get("html", "")
            )
            pattern = r"https?://(?:www\.)?linkedin\.com/in/[\w\-]+"
            matches = re.findall(pattern, content)
            if matches:
                print(f"URL LinkedIn trouvée via recherche directe: {matches[0]}")
                return matches[0]
            return None
        except Exception as e:
            print(f"Erreur recherche LinkedIn directe: {e}")
            return None

    def _normalize(self, s: str) -> str:
        # Basique: minuscule, remplacer espaces/accents, retirer caractères non alphanum
        import unicodedata

        s = unicodedata.normalize("NFKD", s)
        s = "".join(c for c in s if not unicodedata.combining(c))
        s = s.lower().strip()
        s = re.sub(r"[^a-z0-9]+", "-", s)
        s = re.sub(r"-+", "-", s).strip("-")
        return s

    def _build_linkedin_candidates(self, profile) -> List[str]:
        first = self._normalize(profile.first_name)
        last = self._normalize(profile.last_name)
        company = self._normalize(getattr(profile, "company", "") or "")
        base = "https://www.linkedin.com/in"
        candidates = [
            f"{base}/{first}-{last}/",
            f"{base}/{first}.{last}/",
            f"{base}/{first}{last}/",
        ]
        if company:
            candidates.extend(
                [
                    f"{base}/{first}-{last}-{company}/",
                    f"{base}/{first}.{last}.{company}/",
                ]
            )
        # Remove duplicates while preserving order
        seen = set()
        ordered = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                ordered.append(c)
        return ordered

    async def _validate_profile_url(self, url: str) -> bool:
        try:
            result = self.firecrawl.scrape_url(
                url,
                params={
                    "formats": ["markdown"],
                    "onlyMainContent": True,
                    "waitFor": 1500,
                },
            )
            print(
                "[Firecrawl RAW Validate]",
                {
                    "url": url,
                    "has_markdown": bool(result and result.get("markdown")),
                    "markdown_len": len(result.get("markdown", "")) if result else 0,
                },
            )
            content = result.get("markdown", "") if result else ""
            # Heuristic: presence of common LinkedIn terms and name tokens
            if not content or len(content) < 200:
                return False
            score = 0
            for token in ["LinkedIn", "Experience", "Expérience", "About", "À propos"]:
                if token.lower() in content.lower():
                    score += 1
            return score >= 2
        except Exception:
            return False

    async def _scrape_profile_page(self, url: str) -> Dict[str, Any]:
        """
        Scrape la page de profil LinkedIn

        Args:
            url: URL du profil LinkedIn

        Returns:
            Dict avec les données du profil
        """
        print(f"Scraping de la page profil...")

        try:
            # Scraper avec Firecrawl
            result = self.firecrawl.scrape_url(
                url,
                params={
                    "formats": ["markdown", "html"],
                    "onlyMainContent": True,
                    "waitFor": 2000,  # Attendre 2 secondes pour le chargement JS
                },
            )
            print(
                "[Firecrawl RAW Profile]",
                {
                    "url": url,
                    "has_markdown": bool(result and result.get("markdown")),
                    "markdown_len": len(result.get("markdown", "")) if result else 0,
                    "has_html": bool(result and result.get("html")),
                    "html_len": len(result.get("html", "")) if result else 0,
                    "metadata_keys": (
                        list((result.get("metadata") or {}).keys()) if result else []
                    ),
                },
            )

            if not result:
                return {}

            markdown_content = result.get("markdown", "")
            html_content = result.get("html", "")
            metadata = result.get("metadata", {})

            # Parser les informations de base depuis le markdown
            profile_info = self._parse_profile_markdown(markdown_content)

            # Ajouter les métadonnées
            profile_info["metadata"] = metadata
            profile_info["raw_markdown"] = markdown_content[:1000]  # Garder un extrait

            print(f"Profil scrapé: {len(markdown_content)} caractères")

            return profile_info

        except Exception as e:
            print(f"Erreur scraping profil: {e}")
            return {}

    def _parse_profile_markdown(self, markdown: str) -> Dict[str, Any]:
        """
        Parse le markdown pour extraire les informations du profil

        Le markdown LinkedIn contient généralement:
        - Nom
        - Headline (titre)
        - Location
        - About section
        - Experience section
        - Education section
        """
        profile = {}

        lines = markdown.split("\n")

        # Extraction basique (à améliorer selon le format réel)
        current_section = None

        for i, line in enumerate(lines):
            line = line.strip()

            # Détecter les sections
            if "About" in line or "À propos" in line:
                current_section = "about"
            elif "Experience" in line or "Expérience" in line:
                current_section = "experience"
            elif "Education" in line or "Formation" in line:
                current_section = "education"
            elif "Skills" in line or "Compétences" in line:
                current_section = "skills"

            # Extraire le contenu selon la section
            if current_section == "about" and len(line) > 50:
                if "about" not in profile:
                    profile["about"] = line

            # Autres extractions basiques
            # (Le format exact dépendra de ce que Firecrawl retourne)

        # Retourner le contenu brut pour analyse IA
        profile["raw_content"] = markdown

        return profile

    async def _scrape_recent_posts(self, profile_url: str) -> List[Dict]:
        """
        Scrape les posts récents du profil

        LinkedIn structure: /in/username/recent-activity/all/
        """
        print(f"Scraping des posts récents...")

        # Construire l'URL des activités
        if profile_url.endswith("/"):
            activity_url = f"{profile_url}recent-activity/all/"
        else:
            activity_url = f"{profile_url}/recent-activity/all/"

        try:
            result = self.firecrawl.scrape_url(
                activity_url,
                params={
                    "formats": ["markdown"],
                    "onlyMainContent": True,
                    "waitFor": 3000,
                },
            )
            print(
                "[Firecrawl RAW Posts]",
                {
                    "url": activity_url,
                    "has_markdown": bool(result and result.get("markdown")),
                    "markdown_len": len(result.get("markdown", "")) if result else 0,
                },
            )

            if not result or "markdown" not in result:
                print("Impossible de scraper les posts")
                return []

            markdown = result.get("markdown", "")

            # Parser les posts depuis le markdown
            posts = self._parse_posts_from_markdown(markdown)

            print(f"{len(posts)} posts trouvés")

            return posts

        except Exception as e:
            print(f"Erreur scraping posts: {e}")
            # Ne pas bloquer si les posts ne sont pas accessibles
            return []

    def _parse_posts_from_markdown(self, markdown: str) -> List[Dict]:
        """
        Parse les posts depuis le markdown de la page d'activité

        Format typique LinkedIn:
        - Chaque post est souvent séparé
        - Contient du texte, date, likes/comments
        """
        posts = []

        # Split par paragraphes
        sections = markdown.split("\n\n")

        for section in sections:
            section = section.strip()

            # Un post valide a généralement au moins 50 caractères
            if len(section) > 50 and not section.startswith("#"):

                # Essayer d'extraire la date (pattern commun: "il y a X jours/mois")
                date_match = re.search(
                    r"(il y a|ago|hace)\s+(\d+)\s+(jour|day|semaine|week|mois|month)",
                    section,
                    re.IGNORECASE,
                )
                date = date_match.group(0) if date_match else None

                posts.append(
                    {
                        "content": section[:500],  # Limiter à 500 caractères
                        "date": date,
                        "url": None,  # Difficile d'extraire l'URL du post depuis markdown
                    }
                )

        return posts

    async def _scrape_comments(self, posts: List[Dict]) -> List[Dict]:
        """
        Scrape les commentaires sur les posts
        (Optionnel - complexe à implémenter)
        """
        # Pour la v1, on peut skip cette fonctionnalité
        # Car elle nécessite de scraper chaque post individuellement
        return []
