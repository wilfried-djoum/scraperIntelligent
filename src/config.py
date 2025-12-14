"""
Configuration centralisée de l'application
"""

import os
from typing import Optional
from dotenv import load_dotenv, find_dotenv

# Charger le .env automatiquement (cherche dans les répertoires parents)
load_dotenv(find_dotenv())


class Config:
    """Configuration globale de l'application"""

    # APsIGATOIRE)
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY") or ""
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY") or ""
    
    # Debug au chargement
    @classmethod
    def _debug_keys(cls):
        if not cls.FIRECRAWL_API_KEY:
            print("FIRECRAWL_API_KEY non trouvée dans .env")
        else:
            print(f"FIRECRAWL_API_KEY: {cls.FIRECRAWL_API_KEY[:15]}...")
        
        if not cls.OPENAI_API_KEY:
            print("OPENAI_API_KEY non trouvée dans .env")
        else:
            print(f"OPENAI_API_KEY: {cls.OPENAI_API_KEY[:15]}...")

    # Firecrawl Settings
    FIRECRAWL_VERSION: str = "v2"
    FIRECRAWL_TIMEOUT: int = int(os.getenv("FIRECRAWL_TIMEOUT", "30"))
    FIRECRAWL_WAIT_FOR: int = int(os.getenv("FIRECRAWL_WAIT_FOR", "3000"))

    # OpenAI Settings
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE: float = 0.2
    OPENAI_MAX_TOKENS: int = 2000

    # Scraping Settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2  # seconds
    MAX_POSTS_PER_SOURCE: int = 10
    MAX_NEWS_ARTICLES: int = 5

    # Scoring Settings
    MAX_SOURCES_SCORE: int = 40  # 10 points per source, max 4 sources
    MAX_COMPLETENESS_SCORE: int = 60

    @classmethod
    def validate(cls):
        """Valide que les clés API requises sont présentes"""
        if not cls.FIRECRAWL_API_KEY:
            raise ValueError("FIRECRAWL_API_KEY manquante dans .env")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY manquante dans .env")


# Singleton config
config = Config()

# Debug au démarrage
Config._debug_keys()
