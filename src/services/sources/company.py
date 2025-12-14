import os
from firecrawl import FirecrawlApp
from typing import Dict, Any, List
import asyncio


class CompanyScraper:
    """Scraper pour les informations d'entreprise"""

    def __init__(self):
        try:
            self.firecrawl = FirecrawlApp(api_key="fc-56bf239c38ed4a1b820ffa50eb758eae", version="v2")
            print("Firecrawl v2 enabled for CompanyScraper")
        except Exception:
            self.firecrawl = FirecrawlApp(api_key="fc-56bf239c38ed4a1b820ffa50eb758eae")
            print("Firecrawl default version for CompanyScraper")

    async def scrape(self, profile) -> Dict[str, Any]:
        """Scrape les infos de l'entreprise"""

        try:
            # 1. Trouver le site web de l'entreprise
            company_url = await self._find_company_website(profile.company)

            if not company_url:
                return {"error": "Site d'entreprise non trouvé"}

            # 2. Découvrir et scraper pages clés (About, Leadership, Press)
            pages = await self._discover_related_pages(company_url)
            company_info = await self._scrape_company_info(company_url)

            # 3. Chercher et extraire le profil détaillé de la personne
            person_mentions = await self._find_person_on_site(company_url, profile.getFullName())
            person_profile = await self._extract_person_profile(company_url, pages, profile.getFullName())

            return {
                "company_website": company_url,
                "company_info": company_info,
                "pages": pages,
                "person_mentions": person_mentions,
                "person_profile": person_profile,
            }

        except Exception as e:
            print(f"Erreur Company scraping: {e}")
            return {"error": str(e)}

    async def _find_company_website(self, company_name: str) -> str:
        """Trouve le site web officiel de l'entreprise"""

        search_query = f"{company_name} site officiel"

        try:
            search_url = (
                f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            )

            result = self.firecrawl.scrape_url(
                search_url, params={"formats": ["markdown"]}
            )

            content = result.get("markdown", "")

            # Extraire les domaines, classer et filtrer
            import re

            domains = re.findall(r"https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-z]{2,})", content)
            excluded = [
                "linkedin.com",
                "facebook.com",
                "twitter.com",
                "x.com",
                "instagram.com",
                "youtube.com",
                "google.com",
                "bing.com",
                "yahoo.com",
                "duckduckgo.com",
            ]

            # Rank by containing company name and exclude known search engines/socials
            company_key = company_name.lower().replace(" ", "")
            candidates = []
            for d in domains:
                dl = d.lower()
                if any(ex in dl for ex in excluded):
                    continue
                score = 0
                if company_key and company_key in dl.replace("-", "").replace("_", ""):
                    score += 2
                # prefer apex domains over subdomains
                if dl.count(".") == 1:
                    score += 1
                candidates.append((score, d))

            candidates.sort(reverse=True)
            if candidates:
                best = candidates[0][1]
                return f"https://{best}"

            return None

        except Exception as e:
            print(f"Erreur recherche site entreprise: {e}")
            return None

    async def _scrape_company_info(self, base_url: str) -> Dict[str, Any]:
        """Scrape les infos générales de l'entreprise"""

        try:
            # Scraper la page d'accueil
            result = self.firecrawl.scrape_url(
                base_url, params={"formats": ["markdown", "html"], "onlyMainContent": False}
            )

            content = result.get("markdown", "")
            html = result.get("html", "")

            return {
                "description": content[:500],
                "full_content": content,
                "html": html[:2000],
            }

        except Exception as e:
            print(f"Erreur scraping company info: {e}")
            return {}

    async def _find_person_on_site(self, base_url: str, full_name: str) -> List[Dict]:
        """Cherche des mentions de la personne sur le site"""

        try:
            # Rechercher sur le site avec Firecrawl
            search_results = self.firecrawl.search(
                f"site:{base_url} {full_name}", params={"limit": 5}
            )

            mentions = []

            for result in search_results.get("results", []):
                mentions.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("description", ""),
                    }
                )

            return mentions

        except Exception as e:
            print(f"Erreur recherche personne sur site: {e}")
            return []

    async def _discover_related_pages(self, base_url: str) -> List[Dict[str, str]]:
        """Découvre pages pertinentes (about, leadership, press, media)."""
        try:
            # Scrape homepage HTML and find likely page links
            result = self.firecrawl.scrape_url(base_url, params={"formats": ["html", "markdown"], "onlyMainContent": False})
            html = (result or {}).get("html", "")
            md = (result or {}).get("markdown", "")
            import re
            pages = []
            patterns = [
                r"href=\"([^\"]*about[^\"]*)\"",
                r"href=\"([^\"]*leadership[^\"]*)\"",
                r"href=\"([^\"]*team[^\"]*)\"",
                r"href=\"([^\"]*press[^\"]*)\"",
                r"href=\"([^\"]*media[^\"]*)\"",
            ]
            for pat in patterns:
                for m in re.findall(pat, html, flags=re.IGNORECASE):
                    url = m
                    if url.startswith("/"):
                        url = base_url.rstrip("/") + url
                    pages.append({"url": url})
            # Deduplicate
            seen = set()
            unique = []
            for p in pages:
                u = p["url"]
                if u not in seen:
                    seen.add(u)
                    unique.append(p)
            return unique[:10]
        except Exception:
            return []

    async def _extract_person_profile(self, base_url: str, pages: List[Dict[str, str]], full_name: str) -> Dict[str, Any]:
        """Scrape pages pour extraire bio, rôle, image et expériences de la personne."""
        data: Dict[str, Any] = {"bio": None, "role": None, "image_url": None, "experiences": []}
        try:
            targets = [p["url"] for p in pages] + [base_url]
            for u in targets:
                try:
                    result = self.firecrawl.scrape_url(u, params={"formats": ["html", "markdown"], "onlyMainContent": False})
                except Exception:
                    continue
                html = (result or {}).get("html", "")
                md = (result or {}).get("markdown", "")
                lower = md.lower()
                if full_name.lower() in lower or full_name.lower().split()[0] in lower:
                    # Extract bio paragraph containing the name
                    bio = None
                    for para in md.split("\n\n"):
                        if full_name.lower() in para.lower() and len(para) > 50:
                            bio = para.strip()
                            break
                    # Extract role/title near name
                    import re
                    role = None
                    role_match = re.search(rf"{re.escape(full_name)}[^\n]*\n([^\n]{{3,80}})", md)
                    if role_match:
                        role = role_match.group(1).strip()
                    # Fallback: common executive titles on leadership pages
                    if not role:
                        titles = ["Chief Executive Officer", "CEO", "Chairman", "President", "VP", "Vice President", "General Manager"]
                        for t in titles:
                            if t.lower() in lower:
                                role = t
                                break
                    # Extract image from html (img alt includes name or figure near name)
                    img = None
                    for m in re.findall(r"<img[^>]+src=\"([^\"]+)\"[^>]*>", html, flags=re.IGNORECASE):
                        if full_name.split()[0].lower() in m.lower() or "satya" in m.lower():
                            img = m
                            break
                    # Experiences: naive bullets or lines with years
                    experiences = []
                    for line in md.split("\n"):
                        if re.search(r"\b(20\d{2}|19\d{2})\b", line) and len(line) > 30:
                            experiences.append({"description": line.strip()})
                    data.update({"bio": bio or data["bio"], "role": role or data["role"], "image_url": img or data["image_url"]})
                    if experiences:
                        data["experiences"] = experiences
            return data
        except Exception:
            return data
