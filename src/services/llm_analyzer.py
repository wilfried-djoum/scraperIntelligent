"""
Service d'analyse par LLM
Utilise OpenAI GPT pour analyser et structurer les données collectées
"""

import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from src.models.profile import (
    LinkedInPost,
    ReliabilityScore,
    Experience,
)
from src.config import config
from src.config import config


class LLMAnalyzer:
    """Analyseur utilisant un LLM pour traiter les données collectées"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        """
        Initialise l'analyseur LLM

        Args:
            api_key: Clé API OpenAI (utilise OPENAI_API_KEY env var si None)
            model: Modèle à utiliser (gpt-3.5-turbo, gpt-4, gpt-4-turbo, etc.)
        """

        self.api_key = api_key or config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError(
                "Clé API OpenAI manquante. Définir OPENAI_API_KEY dans .env"
            )

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def _call_llm(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.7
    ) -> str:
        """
        Appel générique au LLM

        Args:
            system_prompt: Instructions système pour le LLM
            user_prompt: Prompt utilisateur avec les données
            temperature: Température (0-1, plus bas = plus déterministe)

        Returns:
            Réponse du LLM en texte brut
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=2000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Erreur lors de l'appel au LLM: {e}")
            return ""

    def summarize_post(
        self, post_content: str, post_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Résume un post LinkedIn individuel

        Args:
            post_content: Contenu textuel du post
            post_date: Date du post (optionnel)

        Returns:
            Dict avec 'summary', 'themes', 'engagement_level'
        """
        if not post_content or len(post_content.strip()) < 10:
            return {
                "summary": "Post trop court pour analyse",
                "themes": [],
                "engagement_level": "faible",
            }

        system_prompt = """Tu es un expert en analyse de contenu LinkedIn.
Ta tâche est d'analyser un post et de fournir:
1. Un résumé concis (max 100 mots)
2. Les thématiques principales (2-4 thèmes)
3. Le niveau d'engagement probable (faible/moyen/élevé) basé sur la qualité du contenu

Réponds au format JSON:
{
  "summary": "résumé du post",
  "themes": ["thème1", "thème2"],
  "engagement_level": "moyen"
}"""

        user_prompt = f"Analyse ce post LinkedIn:\n\n{post_content[:2000]}"

        response = self._call_llm(system_prompt, user_prompt, temperature=0.5)

        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # Fallback si le JSON n'est pas valide
            return {
                "summary": response[:200] if response else "Erreur d'analyse",
                "themes": [],
                "engagement_level": "indéterminé",
            }

    def analyze_posts_globally(self, posts: List[LinkedInPost]) -> Dict[str, Any]:
        """
        Analyse globale de tous les posts LinkedIn

        Args:
            posts: Liste des posts avec leurs résumés

        Returns:
            Dict avec recurring_themes, expertise_level, authority_signals, overall_tone, posting_frequency
        """
        if not posts:
            return {
                "recurring_themes": [],
                "expertise_level": "indéterminé",
                "authority_signals": "Aucun post disponible pour analyse",
                "overall_tone": "indéterminé",
                "posting_frequency": "aucune",
            }

        # Préparer le contexte des posts
        posts_context = []
        for i, post in enumerate(posts[:15], 1):  # Limiter à 15 posts max
            posts_context.append(f"Post {i}:")
            posts_context.append(f"Résumé: {post.summary or post.content[:200]}")
            if post.themes:
                posts_context.append(f"Thèmes: {', '.join(post.themes)}")
            posts_context.append("")

        system_prompt = """Tu es un expert en Personal Branding et analyse LinkedIn.
Analyse l'ensemble des posts d'un professionnel et détermine:

1. **recurring_themes**: Liste des 3-5 thématiques récurrentes principales
2. **expertise_level**: Niveau d'expertise démontré (débutant/intermédiaire/expert/leader d'opinion)
3. **authority_signals**: Description des signaux d'autorité (qualité, ton, angle, crédibilité) - 2-3 phrases
4. **overall_tone**: Ton général (professionnel/pédagogique/inspirant/technique/commercial/etc)
5. **posting_frequency**: Fréquence estimée (rare/occasionnel/régulier/fréquent/très fréquent)

Réponds au format JSON:
{
  "recurring_themes": ["thème1", "thème2", "thème3"],
  "expertise_level": "expert",
  "authority_signals": "description des signaux",
  "overall_tone": "professionnel et pédagogique",
  "posting_frequency": "régulier"
}"""

        user_prompt = f"Analyse ces {len(posts)} posts LinkedIn:\n\n" + "\n".join(
            posts_context
        )

        response = self._call_llm(system_prompt, user_prompt, temperature=0.6)

        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            return {
                "recurring_themes": [],
                "expertise_level": "indéterminé",
                "authority_signals": response[:300] if response else "Erreur d'analyse",
                "overall_tone": "indéterminé",
                "posting_frequency": "indéterminée",
            }

    def analyze_reputation(
        self, comments_data: List[str], interactions_data: List[str]
    ) -> Dict[str, Any]:
        """
        Analyse la réputation professionnelle basée sur les commentaires et interactions

        Args:
            comments_data: Liste des commentaires écrits par la personne
            interactions_data: Liste des interactions (réponses, mentions)

        Returns:
            Dict avec quality_score, peer_recognition, interaction_quality, strengths, weak_signals, summary
        """
        if not comments_data and not interactions_data:
            return {
                "quality_score": "indéterminée",
                "peer_recognition": "Pas assez de données",
                "interaction_quality": "Pas de données disponibles",
                "strengths": [],
                "weak_signals": [],
                "summary": "Aucune interaction publique disponible pour analyse",
            }

        # Préparer le contexte
        context_parts = []

        if comments_data:
            context_parts.append("=== COMMENTAIRES ÉCRITS ===")
            for i, comment in enumerate(comments_data[:10], 1):
                context_parts.append(f"Commentaire {i}: {comment[:300]}")

        if interactions_data:
            context_parts.append("\n=== INTERACTIONS ===")
            for i, interaction in enumerate(interactions_data[:10], 1):
                context_parts.append(f"Interaction {i}: {interaction[:300]}")

        system_prompt = """Tu es un expert en réputation professionnelle et analyse comportementale.
Évalue la réputation d'un professionnel basée sur ses commentaires et interactions publiques.

Fournis:
1. **quality_score**: Qualité globale (faible/moyenne/élevée/excellente)
2. **peer_recognition**: Niveau de reconnaissance par les pairs (description 1-2 phrases)
3. **interaction_quality**: Qualité des interactions (description 1-2 phrases)
4. **strengths**: Liste de 2-4 points forts
5. **weak_signals**: Liste de 0-3 signaux faibles ou incohérences (vide si aucun)
6. **summary**: Synthèse globale en 2-3 phrases

Réponds au format JSON:
{
  "quality_score": "élevée",
  "peer_recognition": "description",
  "interaction_quality": "description",
  "strengths": ["point1", "point2"],
  "weak_signals": ["signal1"],
  "summary": "synthèse"
}"""

        user_prompt = "Analyse cette réputation professionnelle:\n\n" + "\n".join(
            context_parts
        )

        response = self._call_llm(system_prompt, user_prompt, temperature=0.6)

        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            return {
                "quality_score": "indéterminée",
                "peer_recognition": "Erreur d'analyse",
                "interaction_quality": "Erreur d'analyse",
                "strengths": [],
                "weak_signals": [],
                "summary": response[:300] if response else "Erreur d'analyse",
            }

    def structure_experiences(
        self, raw_experiences: List[Dict[str, Any]]
    ) -> List[Experience]:
        """
        Structure et enrichit les expériences professionnelles brutes

        Args:
            raw_experiences: Liste d'expériences brutes (dict avec title, company, dates, description)

        Returns:
            Liste d'objets Experience structurés
        """
        if not raw_experiences:
            return []

        structured = []

        for exp in raw_experiences[:10]:  # Limiter à 10 expériences
            # Extraire les données de base
            title = exp.get("title", "")
            company = exp.get("company", "")
            start_date = exp.get("start_date", "")
            end_date = exp.get("end_date", "")
            description = exp.get("description", "")
            location = exp.get("location", "")

            # Utiliser le LLM pour extraire les réalisations clés
            key_achievements = []
            if description and len(description) > 50:
                system_prompt = """Tu es un expert en analyse de parcours professionnel.
Extrait les 2-4 réalisations ou missions clés de cette description d'expérience.
Réponds uniquement avec une liste JSON de strings: ["réalisation1", "réalisation2"]"""

                user_prompt = f"Description de poste:\n{description[:1000]}"
                response = self._call_llm(system_prompt, user_prompt, temperature=0.5)

                try:
                    key_achievements = json.loads(response)
                    if not isinstance(key_achievements, list):
                        key_achievements = []
                except json.JSONDecodeError:
                    # Fallback: extraire les phrases avec des mots-clés
                    key_achievements = []

            # Déterminer si c'est le poste actuel
            is_current = not end_date or end_date.lower() in [
                "présent",
                "present",
                "aujourd'hui",
                "actuel",
                "current",
            ]

            # Calculer la durée si possible
            duration = None
            if start_date:
                if is_current:
                    duration = f"Depuis {start_date}"
                elif end_date:
                    duration = f"{start_date} - {end_date}"

            structured.append(
                Experience(
                    title=title,
                    company=company,
                    start_date=start_date,
                    end_date=end_date if not is_current else None,
                    duration=duration,
                    location=location,
                    description=description[:500] if description else None,
                    key_achievements=key_achievements,
                    is_current=is_current,
                )
            )

        return structured

    def calculate_reliability_score(
        self, profile_data: Dict[str, Any]
    ) -> ReliabilityScore:
        """
        Calcule le score de fiabilité global du profil

        Args:
            profile_data: Dict contenant toutes les données collectées
                - linkedin: données LinkedIn (posts, expériences, etc.)
                - company: données entreprise
                - news: articles de presse
                - social: réseaux sociaux

        Returns:
            Objet ReliabilityScore avec score, justification, factors
        """
        score = 0
        factors = []

        # 1. Vérifier la présence de sources multiples (max 25 points)
        sources_present = []
        if profile_data.get("linkedin"):
            sources_present.append("LinkedIn")
            score += 15
        if profile_data.get("company"):
            sources_present.append("Site entreprise")
            score += 5
        if profile_data.get("news"):
            sources_present.append("Articles de presse")
            score += 10
        if profile_data.get("social"):
            sources_present.append("Réseaux sociaux")
            score += 5

        if len(sources_present) >= 2:
            factors.append(f"Sources multiples vérifiées ({len(sources_present)})")

        # 2. Complétude du profil LinkedIn (max 30 points)
        linkedin_data = profile_data.get("linkedin", {})

        posts = linkedin_data.get("posts", [])
        if len(posts) >= 10:
            score += 15
            factors.append(f"Activité LinkedIn régulière ({len(posts)} posts)")
        elif len(posts) >= 5:
            score += 10
            factors.append(f"Présence LinkedIn active ({len(posts)} posts)")

        experiences = linkedin_data.get("experiences", [])
        if len(experiences) >= 3:
            score += 10
            factors.append(
                f"Parcours professionnel documenté ({len(experiences)} expériences)"
            )
        elif len(experiences) >= 1:
            score += 5

        if linkedin_data.get("profile_complete"):
            score += 5
            factors.append("Profil LinkedIn complet")

        # 3. Cohérence des données (max 25 points)
        # Utiliser le LLM pour détecter les incohérences
        coherence_check = self._check_data_coherence(profile_data)
        if coherence_check.get("is_coherent"):
            score += 20
            factors.append("Cohérence inter-sources validée")
        elif coherence_check.get("minor_issues"):
            score += 10
            factors.append("Cohérence partielle des données")

        # 4. Vérifiabilité (max 20 points)
        if profile_data.get("news") and len(profile_data["news"]) > 0:
            score += 10
            factors.append("Mentions dans la presse vérifiables")

        if linkedin_data.get("has_recommendations"):
            score += 5
            factors.append("Recommandations professionnelles")

        if linkedin_data.get("connections_count", 0) >= 500:
            score += 5
            factors.append("Réseau professionnel étendu")

        # Limiter le score à 100
        score = min(score, 100)

        # Générer une justification détaillée avec le LLM
        justification = self._generate_score_justification(score, factors, profile_data)

        return ReliabilityScore(
            score=score, justification=justification, factors=factors
        )

    def _check_data_coherence(self, profile_data: Dict[str, Any]) -> Dict[str, bool]:
        """Vérifie la cohérence entre les différentes sources de données"""
        linkedin = profile_data.get("linkedin", {})
        company = profile_data.get("company", {})

        # Vérifications simples de cohérence
        coherent = True
        minor_issues = False

        # Vérifier que l'entreprise mentionnée correspond
        current_company = linkedin.get("current_company", "")
        search_company = company.get("name", "")

        if current_company and search_company:
            if (
                current_company.lower() not in search_company.lower()
                and search_company.lower() not in current_company.lower()
            ):
                minor_issues = True
                coherent = False

        return {"is_coherent": coherent, "minor_issues": minor_issues and not coherent}

    def _generate_score_justification(
        self, score: int, factors: List[str], profile_data: Dict[str, Any]
    ) -> str:
        """Génère une justification détaillée du score de fiabilité"""

        system_prompt = """Tu es un expert en évaluation de fiabilité de profils professionnels.
Rédige une justification claire et concise (3-6 lignes) expliquant le score de fiabilité attribué.
Mentionne les points forts et les éventuelles limites."""

        user_prompt = f"""Score attribué: {score}/100

Facteurs positifs:
{chr(10).join('- ' + f for f in factors) if factors else '- Aucun facteur majeur'}

Nombre de sources: {len([k for k, v in profile_data.items() if v])}

Rédige une justification professionnelle."""

        response = self._call_llm(system_prompt, user_prompt, temperature=0.6)

        if response and len(response) > 20:
            return response
        else:
            # Fallback
            if score >= 80:
                return f"Score élevé ({score}/100) grâce à {len(factors)} facteurs de confiance identifiés : données vérifiables sur plusieurs sources et profil professionnel complet."
            elif score >= 60:
                return f"Score correct ({score}/100) avec {len(factors)} facteurs positifs, mais quelques informations manquantes limitent la vérifiabilité complète du profil."
            elif score >= 40:
                return f"Score moyen ({score}/100) : profil partiellement documenté avec {len(factors)} éléments vérifiables, mais manque de diversité des sources."
            else:
                return f"Score faible ({score}/100) : données limitées et difficulté à vérifier les informations sur plusieurs sources indépendantes."

    def enrich_from_knowledge(
        self, first_name: str, last_name: str, company: str
    ) -> Dict[str, Any]:
        """
        Fallback: utilise les connaissances d'entraînement d'OpenAI pour enrichir le profil
        quand le scraping ne retourne pas de données.

        IMPORTANT: Cette méthode ne fait PAS de recherche web en temps réel.
        Elle utilise uniquement les données d'entraînement d'OpenAI (coupure octobre 2023).
        Fonctionne bien pour les personnalités publiques connues.
        Les informations peuvent être obsolètes pour les événements post-octobre 2023.

        Args:
            first_name: Prénom de la personne
            last_name: Nom de famille
            company: Entreprise actuelle

        Returns:
            Dict contenant les champs enrichis depuis les connaissances LLM:
            {
                "headline": str,
                "summary": str,
                "current_role": str,
                "experiences": [Experience],
                "education": [str],
                "skills": [str],
                "notable_achievements": [str],
                "bio_summary": str,
                "_source": "llm_knowledge_base",
                "_warning": "Données issues des connaissances d'entraînement OpenAI"
            }
        """
        system_prompt = """Tu es un assistant spécialisé dans l'extraction d'informations professionnelles publiques.

IMPORTANT:
- Utilise UNIQUEMENT tes connaissances d'entraînement
- Ne fabrique JAMAIS d'informations
- Si tu ne connais pas la personne, retourne tous les champs à null/vides
- Pour les personnalités publiques connues, fournis des informations factuelles vérifiables

Format de réponse JSON strict:
{
    "headline": "Titre professionnel court" ou null,
    "summary": "Biographie professionnelle (2-3 phrases)" ou null,
    "current_role": "Poste actuel" ou null,
    "experiences": [
        {
            "title": "Titre du poste",
            "company": "Entreprise",
            "start_date": "YYYY-MM ou YYYY",
            "end_date": "YYYY-MM ou YYYY ou Present",
            "description": "Description du rôle",
            "is_current": true/false
        }
    ] ou [],
    "education": ["Diplôme - Institution - Année"] ou [],
    "skills": ["Compétence1", "Compétence2"] ou [],
    "notable_achievements": ["Réalisation1", "Réalisation2"] ou [],
    "bio_summary": "Résumé biographique complet" ou null,
    "confidence": "high/medium/low"
}"""

        user_prompt = f"""Personne: {first_name} {last_name}
Entreprise: {company}

Fournis les informations professionnelles publiques connues sur cette personne.
Si tu ne la connais pas, retourne tous les champs à null/vides avec confidence: "low"."""

        try:
            response = self._call_llm(system_prompt, user_prompt, temperature=0.2)
            data = json.loads(response)

            # Ajouter les métadonnées
            data["_source"] = "llm_knowledge_base"
            data["_warning"] = (
                "Données d'entraînement OpenAI (coupure octobre 2023). Informations potentiellement obsolètes pour événements récents (2024-2025)"
            )

            # Convertir experiences en objets Experience si présentes
            if data.get("experiences"):
                experiences_obj = []
                for exp in data["experiences"]:
                    experiences_obj.append(
                        Experience(
                            title=exp.get("title", ""),
                            company=exp.get("company", ""),
                            start_date=exp.get("start_date"),
                            end_date=exp.get("end_date"),
                            description=exp.get("description"),
                            is_current=exp.get("is_current", False),
                        )
                    )
                data["experiences"] = experiences_obj

            return data

        except json.JSONDecodeError as e:
            print(f"Erreur parsing JSON LLM knowledge: {e}")
            return self._get_empty_enrichment_fallback()
        except Exception as e:
            print(f"Erreur enrichissement LLM: {e}")
            return self._get_empty_enrichment_fallback()

    def _get_empty_enrichment_fallback(self) -> Dict[str, Any]:
        """Retourne une structure vide en cas d'erreur"""
        return {
            "headline": None,
            "summary": None,
            "current_role": None,
            "experiences": [],
            "education": [],
            "skills": [],
            "notable_achievements": [],
            "bio_summary": None,
            "confidence": "none",
            "_source": "llm_knowledge_base",
            "_warning": "Échec de l'enrichissement LLM",
            "_error": True,
        }

    def clean_and_structure(self, raw_content: Dict[str, str]) -> Dict[str, Any]:
        """
        Nettoie et structure le contenu brut scrapé pour extraire des informations structurées

        Args:
            raw_content: Dict avec 'markdown' et 'html' du contenu scrapé

        Returns:
            Dict avec headline, summary, skills, experiences, education extraits
        """
        markdown = raw_content.get("markdown", "")
        html = raw_content.get("html", "")

        if not markdown and not html:
            return {}

        system_prompt = """Tu es un expert en extraction d'informations professionnelles.
Analyse le contenu fourni et extrait les informations suivantes au format JSON strict:

{
    "headline": "Titre professionnel court (ex: CEO at Microsoft)" ou null,
    "summary": "Résumé biographique professionnel (2-4 phrases)" ou null,
    "skills": ["Compétence1", "Compétence2", ...] ou [],
    "experiences": [
        {
            "title": "Titre du poste",
            "company": "Nom entreprise",
            "start_date": "YYYY-MM ou YYYY",
            "end_date": "YYYY-MM ou YYYY ou Present",
            "location": "Ville, Pays",
            "description": "Description du rôle"
        }
    ] ou [],
    "education": ["Diplôme - Institution - Année"] ou []
}

IMPORTANT:
- Retourne null pour les champs que tu ne trouves pas
- Ne fabrique JAMAIS d'informations
- Extrait uniquement ce qui est explicitement mentionné"""

        user_prompt = f"""Contenu à analyser:

{markdown[:3000]}

Extrait les informations professionnelles structurées."""

        try:
            response = self._call_llm(system_prompt, user_prompt, temperature=0.2)
            data = json.loads(response)
            return data
        except json.JSONDecodeError as e:
            print(f"Erreur parsing JSON clean_and_structure: {e}")
            return {}
        except Exception as e:
            print(f"Erreur clean_and_structure: {e}")
            return {}

    def summarize_posts(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse et résume une liste de posts LinkedIn

        Args:
            posts: Liste de posts avec 'content', 'date', etc.

        Returns:
            Dict avec summaries, recurring_themes, overall_tone, posting_frequency
        """
        if not posts:
            return {
                "summaries": [],
                "recurring_themes": [],
                "overall_tone": None,
                "posting_frequency": None,
            }

        # Préparer le contexte
        posts_text = []
        for i, post in enumerate(posts[:10], 1):  # Limiter à 10 posts
            content = post.get("content", "")[:500]
            date = post.get("date", "Date inconnue")
            posts_text.append(f"Post {i} ({date}):\n{content}")

        system_prompt = """Tu es un expert en analyse de contenu social media professionnel.
Analyse les posts LinkedIn et fournis:

{
    "summaries": [{"post_index": 1, "summary": "résumé court", "themes": ["thème1"]}],
    "recurring_themes": ["Thème récurrent 1", "Thème 2"],
    "overall_tone": "professionnel/inspirant/technique/thought leadership/...",
    "posting_frequency": "estimation basée sur les dates"
}"""

        user_prompt = "Posts LinkedIn à analyser:\n\n" + "\n\n".join(posts_text)

        try:
            response = self._call_llm(system_prompt, user_prompt, temperature=0.4)
            data = json.loads(response)
            return data
        except:
            return {
                "summaries": [],
                "recurring_themes": [],
                "overall_tone": "indéterminé",
                "posting_frequency": "indéterminée",
            }

    def global_synthesis(
        self, profile_data: Dict[str, Any], sources_used: List[str]
    ) -> Dict[str, Any]:
        """
        Génère une synthèse globale du profil basée sur toutes les données collectées

        Args:
            profile_data: Toutes les données du profil
            sources_used: Liste des sources utilisées

        Returns:
            Dict avec synthesis, strengths, weak_signals, reliability_justification
        """
        system_prompt = """Tu es un expert en analyse de profils professionnels.
Génère une synthèse globale au format JSON:

{
    "synthesis": "Synthèse narrative complète (3-5 phrases) du profil professionnel",
    "strengths": ["Point fort 1", "Point fort 2"],
    "weak_signals": ["Signal d'alerte 1"] ou [],
    "reliability_justification": "Justification de la fiabilité des informations"
}"""

        user_prompt = f"""Profil à synthétiser:
Nom: {profile_data.get('first_name')} {profile_data.get('last_name')}
Entreprise: {profile_data.get('company')}
Titre: {profile_data.get('headline')}
Résumé: {profile_data.get('summary', '')[:500]}
Nombre d'expériences: {len(profile_data.get('experiences', []))}
Publications: {len(profile_data.get('publications', []))}
Posts LinkedIn: {profile_data.get('linkedin_posts_count', 0)}
Sources utilisées: {', '.join(sources_used)}
Score: {profile_data.get('score')}/100

Génère la synthèse globale."""

        try:
            response = self._call_llm(system_prompt, user_prompt, temperature=0.5)
            data = json.loads(response)
            return data
        except:
            return {
                "synthesis": f"Profil professionnel de {profile_data.get('first_name')} {profile_data.get('last_name')} chez {profile_data.get('company')}",
                "strengths": [],
                "weak_signals": [],
                "reliability_justification": "Synthèse automatique indisponible",
            }

    def justify_reliability(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """
        Génère une justification détaillée du score de fiabilité

        Args:
            inputs: Dict avec score, sources, conflicts, coverage, factors

        Returns:
            Dict avec justification et factors list
        """
        score = inputs.get("score", 0)
        sources = inputs.get("sources", [])
        factors = inputs.get("factors", [])

        system_prompt = """Tu es un expert en évaluation de fiabilité de données.
Génère une justification professionnelle du score de fiabilité au format JSON:

{
    "justification": "Justification détaillée et professionnelle du score (2-3 phrases)"
}"""

        user_prompt = f"""Score: {score}/100
Sources: {', '.join(sources)}
Facteurs: {', '.join(factors)}

Rédige une justification professionnelle."""

        try:
            response = self._call_llm(system_prompt, user_prompt, temperature=0.6)
            # Essayer de parser le JSON
            try:
                data = json.loads(response)
                return {"justification": data.get("justification", response)}
            except:
                # Si pas JSON, retourner le texte brut
                return {"justification": response}
        except:
            # Fallback
            if score >= 80:
                return {
                    "justification": f"Score élevé ({score}/100) grâce à {len(factors)} facteurs de confiance identifiés."
                }
            elif score >= 60:
                return {
                    "justification": f"Score correct ({score}/100) avec {len(factors)} facteurs positifs."
                }
            elif score >= 40:
                return {
                    "justification": f"Score moyen ({score}/100) : profil partiellement documenté."
                }
            else:
                return {
                    "justification": f"Score faible ({score}/100) : données limitées."
                }
