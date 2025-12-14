import os
import certifi
from typing import Dict, Any
from firecrawl import FirecrawlApp
from src.config import config


class BaseScraper:
    """Classe de base pour tous les scrapers"""

    def __init__(self, scraper_name: str = "BaseScraper"):
        """
        Initialise le scraper avec Firecrawl

        Args:
            scraper_name: Nom du scraper pour les logs
        """
        self.scraper_name = scraper_name

        # Force trusted CA bundle to avoid SSL issues
        try:
            os.environ.setdefault("SSL_CERT_FILE", certifi.where())
            os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
        except Exception:
            pass

        # Initialize Firecrawl with v2
        try:
            self.firecrawl = FirecrawlApp(
                api_key=config.FIRECRAWL_API_KEY, version=config.FIRECRAWL_VERSION
            )
            print(f"{scraper_name} initialized with Firecrawl v2")
        except Exception as e:
            self.firecrawl = FirecrawlApp(api_key=config.FIRECRAWL_API_KEY)
            print(f"{scraper_name} initialized with Firecrawl default version")

    def _scrape_url(
        self,
        url: str,
        formats: list = None,
        only_main_content: bool = True,
        wait_for: int = None,
    ) -> Any:
        """
        Scrape une URL avec Firecrawl

        Args:
            url: URL à scraper
            formats: Liste des formats à retourner (["markdown", "html"])
            only_main_content: Extraire seulement le contenu principal
            wait_for: Temps d'attente en ms avant scraping

        Returns:
            ScrapeResponse object with .markdown, .html, .metadata attributes
        """
        formats = formats or ["markdown"]
        wait_for = wait_for or config.FIRECRAWL_WAIT_FOR

        try:
            result = self.firecrawl.scrape_url(
                url,
                formats=formats,
                onlyMainContent=only_main_content,
                waitFor=wait_for,
            )
            return result
        except Exception as e:
            print(f"Erreur scraping {url}: {e}")
            return None

    def _get_markdown(self, result: Any, default: str = "") -> str:
        """Extrait le markdown d'un résultat Firecrawl de manière sûre"""
        if result is None:
            return default
        return getattr(result, "markdown", default)

    def _get_html(self, result: Any, default: str = "") -> str:
        """Extrait le HTML d'un résultat Firecrawl de manière sûre"""
        if result is None:
            return default
        return getattr(result, "html", default)

    def _get_metadata(self, result: Any, default: dict = None) -> dict:
        """Extrait les métadonnées d'un résultat Firecrawl de manière sûre"""
        if result is None:
            return default or {}
        return getattr(result, "metadata", default or {})

    async def scrape(self, profile) -> Dict[str, Any]:
        """
        Méthode à implémenter par les scrapers enfants

        Args:
            profile: BaseProfile avec first_name, last_name, company

        Returns:
            Dict contenant les données scrapées
        """
        raise NotImplementedError(
            "Les scrapers doivent implémenter la méthode scrape()"
        )
