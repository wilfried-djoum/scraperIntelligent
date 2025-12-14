from typing import Dict, Any, List
import asyncio
import re
from src.services.base_scraper import BaseScraper


class CompanyScraper(BaseScraper):
    """Scraper pour les informations d'entreprise"""

    def __init__(self):
        super().__init__(scraper_name="CompanyScraper")

    async def scrape(self, profile) -> Dict[str, Any]:
        """Scrape les infos de l'entreprise"""

        try:
            # Trouver le site web de l'entreprise
            company_url = await self._find_company_website(profile.company)

            if not company_url:
                return {"error": "Site d'entreprise non trouvé"}

            # Découvrir et scraper pages clés (About, Leadership, Press)
            pages = await self._discover_related_pages(company_url)
            company_info = await self._scrape_company_info(company_url)

            # Chercher et extraire le profil détaillé de la personne
            person_mentions = await self._find_person_on_site(
                company_url, profile.getFullName()
            )
            person_profile = await self._extract_person_profile(
                company_url, pages, profile.getFullName()
            )

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

            result = self.firecrawl.scrape_url(search_url, formats=["markdown"])

            content = getattr(result, "markdown", "") if result else ""

            # Extraire les domaines, classer et filtrer
            import re

            # Pattern plus strict pour capturer seulement les vrais domaines
            domains = re.findall(
                r"https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-z]{2,}(?:/|$|\s))", content
            )
            excluded = [
                "google",
                "bing",
                "yahoo",
                "duckduckgo",
                "linkedin",
                "facebook",
                "twitter",
                "x.com",
                "instagram",
                "youtube",
                "wikipedia",
                "reddit",
            ]

            # Classement par nom d'entreprise inclus, à l'exclusion des moteurs de recherche et réseaux sociaux connus.
            company_key = company_name.lower().replace(" ", "").replace("-", "")
            candidates = []
            for d in domains:
                dl = d.lower().strip("/").strip()
                # Exclure complètement si contient un mot banni
                if any(ex in dl for ex in excluded):
                    continue
                # Vérifier que c'est un domaine valide (au moins 2 parties)
                parts = dl.split(".")
                if len(parts) < 2:
                    continue
                score = 0
                # Bonus si contient le nom de l'entreprise
                if company_key and company_key in dl.replace("-", "").replace(
                    "_", ""
                ).replace(".", ""):
                    score += 3
                # Préférer les domaines apex (pas de subdomain)
                if len(parts) == 2:
                    score += 2
                # Préférer .com/.fr/.net
                if parts[-1] in ["com", "fr", "net", "org"]:
                    score += 1
                candidates.append((score, dl))

            candidates.sort(reverse=True)
            if candidates and candidates[0][0] > 0:
                best = candidates[0][1]
                # Nettoyer et retourner
                return f"https://{best.strip('/')}"

            # Fallback: essayer de construire le domaine à partir du nom d'entreprise
            if company_name:
                clean = company_name.lower().replace(" ", "").replace("-", "")
                return f"https://{clean}.com"

            return None

        except Exception as e:
            print(f"Erreur recherche site entreprise: {e}")
            return None

    async def _scrape_company_info(self, base_url: str) -> Dict[str, Any]:
        """Scrape les infos générales de l'entreprise"""

        try:
            # Scraper la page d'accueil
            result = self.firecrawl.scrape_url(
                base_url, formats=["markdown", "html"], onlyMainContent=False
            )

            content = getattr(result, "markdown", "") if result else ""
            html = getattr(result, "html", "") if result else ""

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
                f"site:{base_url} {full_name}", limit=5
            )

            mentions = []
            results = getattr(search_results, "results", []) if search_results else []
            for result in results:
                mentions.append(
                    {
                        "title": getattr(result, "title", ""),
                        "url": getattr(result, "url", ""),
                        "snippet": getattr(result, "description", ""),
                    }
                )

            return mentions

        except Exception as e:
            print(f"Erreur recherche personne sur site: {e}")
            return []

    async def _discover_related_pages(self, base_url: str) -> List[Dict[str, str]]:
        """Découvre pages pertinentes (about, leadership, press, media)."""
        try:
            # Scrape homepage HTML et trouver les liens pertinents
            result = self.firecrawl.scrape_url(
                base_url,
                params={"formats": ["html", "markdown"], "onlyMainContent": False},
            )
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

    async def _extract_person_profile(
        self, base_url: str, pages: List[Dict[str, str]], full_name: str
    ) -> Dict[str, Any]:
        """Scrape pages pour extraire bio, rôle, image et expériences de la personne."""
        data: Dict[str, Any] = {
            "bio": None,
            "role": None,
            "image_url": None,
            "experiences": [],
        }
        try:
            targets = [p["url"] for p in pages] + [base_url]
            for u in targets:
                try:
                    result = self.firecrawl.scrape_url(
                        u, formats=["html", "markdown"], onlyMainContent=False
                    )
                except Exception:
                    continue
                html = getattr(result, "html", "") if result else ""
                md = getattr(result, "markdown", "") if result else ""
                lower = md.lower()
                if full_name.lower() in lower or full_name.lower().split()[0] in lower:
                    # Extract bio: paragraphes contenant le nom complet
                    bio = None
                    for para in md.split("\n\n"):
                        if full_name.lower() in para.lower() and len(para) > 50:
                            bio = para.strip()
                            break
                    # Extract role: ligne après le nom complet
                    import re

                    role = None
                    role_match = re.search(
                        rf"{re.escape(full_name)}[^\n]*\n([^\n]{{3,80}})", md
                    )
                    if role_match:
                        role = role_match.group(1).strip()
                    # Fallback: titres exécutifs courants sur les pages de direction
                    if not role:
                        titles = [
                            "Chief Executive Officer",
                            "CEO",
                            "Chairman",
                            "President",
                            "VP",
                            "Vice President",
                            "General Manager",
                        ]
                        for t in titles:
                            if t.lower() in lower:
                                role = t
                                break
                    # Extract image from html
                    img = None
                    for m in re.findall(
                        r"<img[^>]+src=\"([^\"]+)\"[^>]*>", html, flags=re.IGNORECASE
                    ):
                        if (
                            full_name.split()[0].lower() in m.lower()
                            or "satya" in m.lower()
                        ):
                            img = m
                            break
                    # Experiences: naive bullets or lines with years
                    experiences = []
                    for line in md.split("\n"):
                        if re.search(r"\b(20\d{2}|19\d{2})\b", line) and len(line) > 30:
                            experiences.append({"description": line.strip()})
                    data.update(
                        {
                            "bio": bio or data["bio"],
                            "role": role or data["role"],
                            "image_url": img or data["image_url"],
                        }
                    )
                    if experiences:
                        data["experiences"] = experiences
            return data
        except Exception:
            return data
