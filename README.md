# ScraperIntelligent

API de profiling professionnel intelligent combinant web scraping et analyse LLM.

## 📋 Architecture Refactorisée

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

## 🏗️ Améliorations du Refactoring

### 1. Configuration Centralisée (`src/config.py`)
- ✅ Toutes les clés API dans un seul endroit
- ✅ Variables d'environnement avec valeurs par défaut
- ✅ Configuration Firecrawl (version, timeout, wait_for)
- ✅ Configuration OpenAI (model, temperature, max_tokens)
- ✅ Paramètres de scraping (retries, max posts, etc.)

### 2. Classe de Base `BaseScraper` (`src/services/base_scraper.py`)
- ✅ Factorisation de l'initialisation Firecrawl
- ✅ Gestion SSL/CA bundle centralisée
- ✅ Méthodes helper pour extraction sûre (markdown, html, metadata)
- ✅ Méthode `_scrape_url()` générique
- ✅ Logs cohérents

### 3. Orchestrateur `ProfileOrchestrator` (`src/services/profile_orchestrator.py`)
- ✅ Extraction de toute la logique métier hors de main.py
- ✅ Workflow découpé en méthodes privées claires:
  - `_scrape_all_sources()` - Lance les scrapers
  - `_extract_profile_data()` - Extrait et structure les données
  - `_calculate_reliability()` - Calcule le score
  - `_assemble_profile()` - Assemble le profil final
- ✅ Séparation des préoccupations (scraping / extraction / enrichissement / scoring)
- ✅ Testabilité améliorée

### 4. Main.py Simplifié
- ✅ Réduit de ~340 lignes à 60 lignes (-82%)
- ✅ Responsabilité unique: routing FastAPI
- ✅ Délégation complète à l'orchestrateur
- ✅ Documentation API améliorée

## 🚀 Installation

```bash
# Cloner le repo
cd ScraperIntelligent

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement (optionnel)
cp .env.example .env
# Éditer .env avec vos clés API
```

## ⚙️ Configuration

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

## 🏃‍♂️ Lancement

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API accessible sur:
- Interface Web: http://localhost:8000/static/index.html
- API Docs: http://localhost:8000/docs
- Endpoint profiling: POST http://localhost:8000/profiling/

## 📡 Usage de l'API

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

## 🔧 Points Techniques Importants

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

## ⚠️ Limitations Connues

1. **LinkedIn** - 403 Forbidden pour la plupart des profils (Anti-scraping)
2. **LLM Knowledge** - Données jusqu'à octobre 2023 seulement
3. **Scraping** - Dépend de la structure HTML des sites (peut casser)
4. **Rate Limiting** - Firecrawl a des limites API

## 🧪 Tests

```bash
# Lancer un test avec une personnalité publique connue
curl -X POST http://localhost:8000/profiling/ \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Satya", "last_name": "Nadella", "company": "Microsoft"}'
```

## 📚 Prochaines Améliorations

- [ ] Tests unitaires pour chaque service
- [ ] Cache Redis pour éviter de re-scraper
- [ ] Rate limiting par IP
- [ ] Retry automatique avec backoff exponentiel
- [ ] Logging structuré (JSON logs)
- [ ] Monitoring (Prometheus/Grafana)
- [ ] Migration des clés API en prod vers variables d'env uniquement
- [ ] Support de recherche web temps réel (Tavily/Perplexity API)
- [ ] Amélioration du parsing HTML avec sélecteurs CSS

## 📄 License

MIT
