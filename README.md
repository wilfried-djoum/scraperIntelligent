# ScraperIntelligent

API de profiling professionnel intelligent combinant web scraping et analyse LLM.

### 1. Démo Fonctionnelle

**Exécution en local:**
```bash
# Cloner le repository
git clone <repo-url>
cd ScraperIntelligent

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
# Créer un fichier .env à la racine avec:
# FIRECRAWL_API_KEY=votre_clé
# OPENAI_API_KEY=votre_clé

# Lancer l'application
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Accéder à l'interface web
# http://localhost:8000/static/index.html
```

**Déploiement (Vercel/Heroku/Railway):**
- Voir [DEPLOYMENT.md](DEPLOYMENT.md) pour les instructions détaillées
- Configuration des variables d'environnement requise
- Compatible avec Docker (Dockerfile inclus)

### 2. Code Propre et Structuré

**Qualité du code:**
- ✓ Architecture modulaire (Orchestrator pattern)
- ✓ Séparation des responsabilités (services, models, config)
- ✓ Main.py réduit de 82% (340 → 59 lignes)
- ✓ Commentaires docstrings sur toutes les fonctions publiques
- ✓ Type hints Python (Pydantic models)
- ✓ Configuration centralisée (.env + config.py)
- ✓ Gestion d'erreurs cohérente

**Standards suivis:**
- PEP 8 (formatting Python)
- Single Responsibility Principle
- DRY (Don't Repeat Yourself) via BaseScraper
- Dependency Injection (config singleton)

### 3. Documentation Technique

**Documents fournis:**
- [README.md](README.md) - Vue d'ensemble et guide de démarrage rapide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture détaillée et diagrammes
- Commentaires inline dans le code source

**Couverture:**
- ✓ Architecture système (patterns, flux de données)
- ✓ Choix techniques justifiés (Firecrawl, OpenAI, FastAPI)
- ✓ Limites actuelles documentées
- ✓ Pistes d'amélioration priorisées

---

## Architecture Refactorisée

### Structure du Projet

```
ScraperIntelligent/
├── main.py                          # Point d'entrée FastAPI (60 lignes)
├── requirements.txt
├── src/
│   ├── config.py                    # Configuration centralisée
│   ├── models/
│   │   └── profile.py               # Modèles Pydantic
│   ├── services/
│   │   ├── base_scraper.py          # Classe de base pour scrapers
│   │   ├── profile_orchestrator.py  # Orchestration du workflow
│   │   ├── llm_analyzer.py          # Service LLM OpenAI
│   │   ├── scoring.py               # Calcul du score de fiabilité
│   │   └── sources/
│   │       ├── linkedin.py          # Scraper LinkedIn
│   │       ├── company.py           # Scraper sites entreprise
│   │       ├── news.py              # Scraper presse
│   │       └── social.py            # Scraper réseaux sociaux
│   └── static/
│       ├── index.html
│       ├── main.js
│       └── styles.css
```

## Améliorations du Refactoring

### 1. Configuration Centralisée (`src/config.py`)
- Toutes les clés API dans un seul endroit
- Variables d'environnement avec valeurs par défaut
- Configuration Firecrawl (version, timeout, wait_for)
- Configuration OpenAI (model, temperature, max_tokens)
- Paramètres de scraping (retries, max posts, etc.)

### 2. Classe de Base `BaseScraper` (`src/services/base_scraper.py`)
- Factorisation de l'initialisation Firecrawl
- Gestion SSL/CA bundle centralisée
- Méthodes helper pour extraction sûre (markdown, html, metadata)
- Méthode `_scrape_url()` générique
- Logs cohérents

### 3. Orchestrateur `ProfileOrchestrator` (`src/services/profile_orchestrator.py`)
- Extraction de toute la logique métier hors de main.py
- Workflow découpé en méthodes privées claires:
  - `_scrape_all_sources()` - Lance les scrapers
  - `_extract_profile_data()` - Extrait et structure les données
  - `_calculate_reliability()` - Calcule le score
  - `_assemble_profile()` - Assemble le profil final
- Séparation des préoccupations (scraping / extraction / enrichissement / scoring)
- Testabilité améliorée

### 4. Main.py Simplifié
- Réduit de ~340 lignes à 60 lignes (-82%)
- Responsabilité unique: routing FastAPI
- Délégation complète à l'orchestrateur
- Documentation API améliorée

## Installation

```bash
# Cloner le repo
cd ScraperIntelligent

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement (optionnel)
cp .env.example .env
# Éditer .env avec vos clés API
```

## Configuration

### Variables d'Environnement

Créer un fichier `.env` à la racine:

```env
# API Keys
FIRECRAWL_API_KEY=your_firecrawl_key
OPENAI_API_KEY=your_openai_key

# Firecrawl Settings
FIRECRAWL_TIMEOUT=30
FIRECRAWL_WAIT_FOR=3000

# OpenAI Settings
OPENAI_MODEL=gpt-4o-mini
```

Les clés sont également hardcodées dans `src/config.py` pour le développement (à retirer en production).

## Lancement

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API accessible sur:
- Interface Web: http://localhost:8000/static/index.html
- API Docs: http://localhost:8000/docs
- Endpoint profiling: POST http://localhost:8000/profiling/

## Usage de l'API

### Endpoint `/profiling/`

**Request:**
```json
POST /profiling/
{
    "first_name": "Satya",
    "last_name": "Nadella",
    "company": "Microsoft"
}
```

**Response:**
```json
{
    "debug": {
        "sources_used": ["linkedin", "company", "news", "social"],
        "processing_time": "34.2s"
    },
    "profile": {
        "first_name": "Satya",
        "last_name": "Nadella",
        "company": "Microsoft",
        "headline": "CEO at Microsoft",
        "summary": "...",
        "current_role": "Chief Executive Officer",
        "experiences": [...],
        "skills": [...],
        "education": [...],
        "publications": [...],
        "linkedin_analysis": {...},
        "contact_info": {...},
        "reliability": {
            "score": 85,
            "justification": "...",
            "factors": [...]
        },
        "reputation": {...},
        "sources_used": [...]
    }
}
```

## 🔧 Choix Techniques

### Framework Backend: FastAPI
**Pourquoi FastAPI?**
- Performance élevée (basé sur Starlette + Pydantic)
- Documentation API automatique (Swagger UI)
- Type safety native avec Python type hints
- Async/await pour I/O non-bloquant
- Facilité de déploiement

### Scraping: Firecrawl v2
**Pourquoi Firecrawl?**
- API managée (pas de maintenance de navigateurs headless)
- Support JavaScript rendering
- Rate limiting géré côté serveur
- Extraction markdown/html structurée
- Alternative à Selenium/Playwright plus simple

### LLM: OpenAI gpt-4o-mini
**Pourquoi gpt-4o-mini?**
- Coût optimisé (5-10x moins cher que GPT-4)
- Latence réduite (~2-3s par requête)
- Capacités de structuration suffisantes
- Fallback sur knowledge base (Oct 2023)
- Alternative: Claude-3.5-Sonnet, Mistral, Llama-3

### Architecture: Orchestrator Pattern
**Pourquoi ce pattern?**
- Séparation claire des responsabilités
- Workflow complexe coordonné (4 scrapers → extraction → LLM → scoring)
- Testabilité (chaque service isolé)
- Évolutivité (ajout de nouvelles sources facile)

### Frontend: Vanilla JS
**Pourquoi pas React/Vue?**
- Pas de build step nécessaire
- Déploiement statique simple
- Overhead minimal pour une SPA simple
- Chargement instantané

## Points Techniques Importants

### Firecrawl v2
Tous les scrapers utilisent maintenant Firecrawl v2:
```python
self.firecrawl = FirecrawlApp(api_key=config.FIRECRAWL_API_KEY, version="v2")
result = self.firecrawl.scrape_url(url, formats=["markdown"], onlyMainContent=True)
markdown = getattr(result, 'markdown', '')  # Accès via attributs, pas dict
```

### OpenAI LLM
- Modèle: **gpt-4o-mini** (coupure octobre 2023)
- Utilisations:
  1. `clean_and_structure()` - Extraction structurée du contenu scrapé
  2. `summarize_posts()` - Analyse des posts LinkedIn
  3. `global_synthesis()` - Synthèse narrative du profil
  4. `justify_reliability()` - Justification du score
  5. `enrich_from_knowledge()` - **Fallback** si scraping échoue (données 2023 uniquement)

### Score de Fiabilité
- Base 0-100
- **Sources** (max 40 pts): +10 par source (LinkedIn/Company/News/Social)
- **Complétude** (max 60 pts): headline(8), summary(10), experiences(12), publications(8), posts(8), education(6), skills(4), social(4)
- Pénalité si données LLM avec faible confiance

## Limites Actuelles

### 1. Scraping LinkedIn
**Problème:** 403 Forbidden pour la plupart des profils publics  
**Cause:** Anti-scraping agressif de LinkedIn (Cloudflare, CAPTCHA)  
**Impact:** Données LinkedIn limitées ou absentes  
**Workaround:** Enrichissement LLM fallback (données Oct 2023)

### 2. Connaissance LLM Datée
**Problème:** gpt-4o-mini coupure octobre 2023  
**Cause:** Limitation intrinsèque du modèle  
**Impact:** Informations récentes (2024-2025) non disponibles via fallback  
**Workaround:** Scraping web reste la source primaire

### 3. Fragilité du Scraping HTML
**Problème:** Sites peuvent changer leur structure  
**Cause:** Pas d'API officielle, parsing HTML  
**Impact:** Scrapers peuvent casser sans préavis  
**Workaround:** Logs détaillés + monitoring + retry logic

### 4. Rate Limiting
**Problème:** Firecrawl et OpenAI ont des quotas  
**Cause:** Plans API limités  
**Impact:** Erreurs 429 en production haute charge  
**Workaround:** Cache Redis + backoff exponentiel (roadmap)

### 5. Performance
**Problème:** Temps de réponse 30-45s par profil  
**Cause:** 4 scrapers séquentiels + 5 appels LLM  
**Impact:** UX dégradée pour l'utilisateur  
**Workaround:** Loader animé + parallélisation (roadmap)

## Pistes d'Amélioration

### Court Terme (1-2 semaines)
**Priorité HAUTE:**
- [ ] **Parallélisation des scrapers** → Réduire temps à ~15-20s
  - Utiliser `asyncio.gather()` pour scrapers indépendants
  - Gains: 50% temps de réponse

- [ ] **Cache Redis** → Éviter re-scraping
  - TTL 24h pour profils
  - Gains: 90% réduction coûts API

- [ ] **Tests unitaires** → Garantir stabilité
  - Coverage 80%+ sur services
  - CI/CD avec GitHub Actions

**Priorité MOYENNE:**
- [ ] **Retry automatique** → Resilience
  - Backoff exponentiel (1s, 2s, 4s)
  - Circuit breaker pattern

- [ ] **Logging structuré** → Debuggabilité
  - JSON logs avec contexte
  - Agrégation Datadog/Sentry

### Moyen Terme (1-2 mois)
**Fonctionnalités:**
- [ ] **API de recherche temps réel** → Données fraîches
  - Intégration Tavily/Perplexity
  - Données post-Oct 2023

- [ ] **Webhooks** → Async profiling
  - Callback URL fournie par client
  - Profiling en arrière-plan

- [ ] **Multi-profils batch** → Scalabilité
  - Upload CSV → API traite liste
  - Rate limiting intelligent

**Infrastructure:**
- [ ] **Monitoring** → Observabilité
  - Prometheus + Grafana
  - Alerting Slack/PagerDuty

- [ ] **Rate limiting par IP** → Protection
  - SlowAPI middleware
  - Quotas par tier (free/pro)

### Long Terme (3-6 mois)
**R&D:**
- [ ] **Fine-tuning LLM** → Précision
  - Dataset propriétaire de profils
  - Modèle spécialisé extraction

- [ ] **Graph database** → Relations
  - Neo4j pour liens entre profils
  - Analyse réseau

- [ ] **Computer Vision** → OCR certificats
  - Extraction diplômes/certificats PDF
  - Validation automatique

## Tests

### Test Manuel Rapide
```bash
# Lancer un test avec une personnalité publique connue
curl -X POST http://localhost:8000/profiling/ \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Satya", "last_name": "Nadella", "company": "Microsoft"}'

# Résultat attendu: Score 70-90/100, données partielles (LinkedIn bloqué)
```

### Tests Unitaires (À venir)
```bash
pip install pytest pytest-asyncio pytest-cov
pytest tests/ --cov=src --cov-report=html
```