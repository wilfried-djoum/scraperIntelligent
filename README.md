# ScraperIntelligent

API de profiling professionnel intelligent combinant web scraping et analyse LLM.

## Démarrage Rapide

```bash
# Installation
pip install -r requirements.txt

# Configuration (.env)
FIRECRAWL_API_KEY=votre_clé
OPENAI_API_KEY=votre_clé

# Lancement
uvicorn main:app --reload --port 8000
```

**Endpoints :** `http://localhost:8000/docs` | `http://localhost:8000/static/index.html`

---

## Architecture

**Pattern : Orchestrator**
- `ProfileOrchestrator` : coordonne le workflow (scraping → extraction → scoring → assemblage)
- `BaseScraper` : classe de base pour tous les scrapers (Firecrawl v2)
- `LLMAnalyzer` : service d'analyse via OpenAI
- `ReliabilityScorer` : calcul du score de fiabilité (0-100)

**Structure modulaire :**
```
src/
├── config.py                    # Configuration centralisée
├── models/profile.py            # Modèles Pydantic
├── services/
│   ├── profile_orchestrator.py  # Orchestration du workflow
│   ├── llm_analyzer.py          # Service LLM OpenAI
│   ├── scoring.py               # Calcul du score
│   └── sources/                 # Scrapers (LinkedIn, Company, News, Social)
```

## Choix Techniques

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| **Backend** | FastAPI | Performance async, documentation auto, type hints |
| **Scraping** | Firecrawl v2 | API managée, JS rendering, pas de maintenance browser |
| **LLM** | OpenAI gpt-4o-mini | Coût optimisé (5-10x vs GPT-4), latence ~2s, fallback sur knowledge base |
| **Scoring** | Règles métier | 0-100 basé sur sources (40 pts) + complétude (60 pts) |

**Workflow LLM (5 utilisations) :**
1. Extraction structurée du contenu scrapé
2. Analyse des posts LinkedIn
3. Synthèse narrative du profil
4. Justification du score de fiabilité
5. Enrichissement via knowledge base (fallback Oct 2023)
- Évolutivité (ajout de nouvelles sources facile)

### Frontend: Vanilla JS
**Pourquoi pas React/Vue?**
- Pas de build step nécessaire
- Déploiement statique simple
## Limites & Améliorations

### Limites Actuelles

| Problème | Impact | Workaround |
|----------|--------|------------|
| **LinkedIn bloqué** | 403 Forbidden (Cloudflare/CAPTCHA) | Enrichissement LLM fallback (données Oct 2023) |
| **LLM daté** | gpt-4o-mini coupure Oct 2023 | Scraping web source primaire |
| **Performance** | 30-45s par profil (4 scrapers + 5 LLM) | Loader animé + parallélisation (roadmap) |
| **Rate limiting** | Quotas Firecrawl/OpenAI | Cache Redis (roadmap) |
| **Fragilité scraping** | Sites changent leur structure | Logs + monitoring + retry logic |

### Pistes d'Amélioration

**Priorité HAUTE :**
- [ ] Parallélisation scrapers (`asyncio.gather()`) → -50% temps réponse
- [ ] Cache Redis (TTL 24h) → -90% coûts API
- [ ] Tests unitaires (coverage 80%+) + CI/CD

**Priorité MOYENNE :**
- [ ] Retry automatique + backoff exponentiel
- [ ] Logging structuré (JSON) + Sentry/Datadog*Backend** | FastAPI | Performance async, documentation auto, type hints |
| **Scraping** | Firecrawl v2 | API managée, JS rendering, pas de maintenance browser |
| **LLM** | OpenAI gpt-4o-mini | Coût optimisé (5-10x vs GPT-4), latence ~2s, fallback sur knowledge base |
| **Scoring** | Règles métier | 0-100 basé sur sources (40 pts) + complétude (60 pts) |