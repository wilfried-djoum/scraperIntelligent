"""
Service orchestrateur pour le profiling complet
Extrait la logique métier de main.py
"""

import time
from typing import Dict, Any
from src.models.profile import (
    BaseProfile,
    EnrichedProfile,
    LinkedInAnalysis,
    LinkedInPost,
    ReputationAnalysis,
    ContactInfo,
    ReliabilityScore,
    Experience,
)
from src.services.sources.linkedin import LinkedInScraper
from src.services.sources.company import CompanyScraper
from src.services.sources.news import NewsScraper
from src.services.sources.social import SocialScraper
from src.services.llm_analyzer import LLMAnalyzer
from src.services.scoring import ReliabilityScorer


class ProfileOrchestrator:
    """Orchestre le processus complet de profiling"""

    def __init__(self):
        """Initialise tous les services nécessaires"""
        self.linkedin = LinkedInScraper()
        self.company = CompanyScraper()
        self.news = NewsScraper()
        self.social = SocialScraper()
        self.llm = LLMAnalyzer()

    async def create_profile(self, data: BaseProfile) -> Dict[str, Any]:
        """
        Crée un profil enrichi complet via workflow orchestré
        
        Workflow en 5 phases:
        1. Scraping multi-sources (LinkedIn, Company, News, Social)
        2. Extraction et structuration des données (avec LLM)
        3. Enrichissement des champs manquants (fallback LLM)
        4. Calcul du score de fiabilité (0-100)
        5. Assemblage du profil final

        Args:
            data: BaseProfile avec first_name, last_name, company

        Returns:
            Dict {
                "debug": {"sources_used": [...], "processing_time": "42s"},
                "profile": EnrichedProfile {...}
            }
            
        Raises:
            Exception: Si toutes les sources de scraping échouent
        """
        start = time.time()

        # PHASE 1: Scraper toutes les sources en parallèle (40-50s)
        scraping_results = await self._scrape_all_sources(data)

        # 2. Extraire et enrichir les données
        profile_data = await self._extract_profile_data(data, scraping_results)

        # 3. Calculer le score de fiabilité
        reliability = self._calculate_reliability(profile_data)

        # 4. Assembler le profil final
        profile_obj = self._assemble_profile(data, profile_data, reliability)

        processing_time = round(time.time() - start, 2)

        return {
            "debug": {
                "sources_used": profile_data["sources_used"],
                "processing_time": f"{processing_time}s",
            },
            "profile": profile_obj,
        }

    async def _scrape_all_sources(self, profile: BaseProfile) -> Dict[str, Any]:
        """Lance tous les scrapers en parallèle"""
        print(f"\n🔍 Scraping pour {profile.getFullName()}...\n")

        li_result = await self.linkedin.scrape(profile)
        company_result = await self.company.scrape(profile)
        news_result = await self.news.scrape(profile)
        social_result = await self.social.scrape(profile)

        return {
            "linkedin": li_result,
            "company": company_result,
            "news": news_result,
            "social": social_result,
        }

    async def _extract_profile_data(
        self, profile: BaseProfile, scraping_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extrait et structure toutes les données des résultats de scraping"""

        li_result = scraping_results["linkedin"]
        company_result = scraping_results["company"]
        news_result = scraping_results["news"]
        social_result = scraping_results["social"]

        # Sources utilisées
        sources_used = self._identify_sources(scraping_results)

        # Headline & Summary
        headline, summary = self._extract_headline_summary(
            profile, company_result, li_result
        )

        # LLM enrichment si besoin
        structured, llm_enrichment = await self._enrich_with_llm(
            profile, headline, summary, company_result
        )

        # Merge headline/summary après LLM avec fallbacks
        headline = (
            headline or structured.get("headline") or llm_enrichment.get("headline") or 
            f"Professionnel chez {profile.company}"
        )
        summary = (
            summary or structured.get("summary") or llm_enrichment.get("summary") or 
            f"{profile.first_name} {profile.last_name} travaille chez {profile.company}."
        )

        # Current role
        current_role = self._extract_current_role(company_result, llm_enrichment)

        # Experiences (toujours retourner une liste)
        experiences = self._extract_experiences(
            profile, company_result, structured, llm_enrichment
        ) or []

        # Education & Skills (toujours retourner des listes)
        education = self._extract_education(structured, llm_enrichment) or []
        skills = self._extract_skills(structured, llm_enrichment) or []

        # Publications & Speaking (toujours retourner des listes)
        publications = self._extract_publications(news_result) or []
        speaking_engagements = self._extract_speaking(company_result) or []

        # LinkedIn posts & analysis (gérer le cas où None est retourné)
        linkedin_analysis = self._analyze_linkedin_posts(li_result)
        if linkedin_analysis is None:
            from src.models.profile import LinkedInAnalysis
            linkedin_analysis = LinkedInAnalysis(posts=[], themes=[], engagement_level="unknown")

        # Contact info
        contact_info = self._extract_contact_info(
            li_result, company_result, social_result
        )

        # Global synthesis (score sera calculé après)
        try:
            synthesis = self._generate_synthesis(
                profile,
                headline,
                summary,
                experiences,
                publications,
                linkedin_analysis,
                sources_used,
                0,  # score sera mis à jour dans l'assemblage final
            )
        except Exception as e:
            print(f"Erreur lors de la génération de la synthèse: {e}")
            synthesis = {
                "synthesis": f"Profil de {profile.first_name} {profile.last_name} chez {profile.company}. Données limitées disponibles.",
                "strengths": [],
                "weak_signals": [],
                "reliability_justification": "Données limitées pour ce profil."
            }

        return {
            "sources_used": sources_used,
            "headline": headline,
            "summary": summary,
            "current_role": current_role,
            "experiences": experiences,
            "education": education,
            "skills": skills,
            "publications": publications,
            "speaking_engagements": speaking_engagements,
            "linkedin_analysis": linkedin_analysis,
            "contact_info": contact_info,
            "synthesis": synthesis,
            "llm_enrichment": llm_enrichment,
        }

    def _identify_sources(self, results: Dict[str, Any]) -> list:
        """Identifie les sources ayant retourné des données"""
        sources = []
        if results["linkedin"].get("url"):
            sources.append("linkedin")
        if results["company"].get("company_website"):
            sources.append("company")
        if results["news"].get("total_mentions"):
            sources.append("news")
        if results["social"]:
            sources.append("social")
        return sources

    def _extract_headline_summary(
        self, profile: BaseProfile, company_result: Dict, li_result: Dict
    ) -> tuple:
        """Extrait headline et summary des résultats de scraping"""
        headline = None
        summary = None

        # From company page
        if company_result.get("company_info", {}).get("full_content"):
            content = company_result["company_info"]["full_content"]
            full_name = profile.getFullName()
            for para in content.split("\n\n"):
                if full_name.lower() in para.lower():
                    summary = para.strip()[:400]
                    break

        # Fallback: bio from company person_profile
        if not summary and company_result.get("person_profile", {}).get("bio"):
            summary = company_result["person_profile"]["bio"]

        # Fallback: LinkedIn about
        if not summary and li_result.get("profile", {}).get("about"):
            summary = li_result["profile"]["about"]

        return headline, summary

    async def _enrich_with_llm(
        self,
        profile: BaseProfile,
        headline: str,
        summary: str,
        company_result: Dict,
    ) -> tuple:
        """Enrichit les données via LLM si nécessaire"""
        structured = {}
        llm_enrichment = {}

        # Structure from scraped content
        if not headline or not summary:
            structured = (
                self.llm.clean_and_structure(
                    {
                        "markdown": company_result.get("company_info", {}).get(
                            "full_content", ""
                        ),
                        "html": company_result.get("company_info", {}).get("html", ""),
                    }
                )
                or {}
            )

        # Fallback: LLM knowledge base
        if not headline and not summary:
            print("Fallback: enrichissement via LLM knowledge base (oct 2023)...")
            llm_enrichment = self.llm.enrich_from_knowledge(
                profile.first_name, profile.last_name, profile.company
            )

            if llm_enrichment.get("confidence") in ["high", "medium"]:
                print(
                    f"Enrichissement LLM réussi (confidence: {llm_enrichment.get('confidence')})"
                )
            else:
                print("Enrichissement LLM avec faible confiance ou échec")

        return structured, llm_enrichment

    def _extract_current_role(self, company_result: Dict, llm_enrichment: Dict) -> str:
        """Extrait le rôle actuel"""
        current_role = company_result.get("person_profile", {}).get("role")
        if not current_role and llm_enrichment.get("current_role"):
            current_role = llm_enrichment.get("current_role")
        return current_role or "Poste non spécifié"

    def _extract_experiences(
        self,
        profile: BaseProfile,
        company_result: Dict,
        structured: Dict,
        llm_enrichment: Dict,
    ) -> list:
        """Extrait et merge les expériences de toutes les sources"""
        experiences = []

        # From company person_profile
        for exp in (
            company_result.get("person_profile", {}).get("experiences", []) or []
        ):
            try:
                experiences.append(
                    Experience(
                        title=exp.get("title") or "",
                        company=profile.company,
                        description=exp.get("description"),
                    )
                )
            except Exception:
                continue

        # From structured content
        for exp in (structured.get("experiences") or []) if structured else []:
            try:
                experiences.append(
                    Experience(
                        title=exp.get("title") or "",
                        company=exp.get("company") or profile.company,
                        start_date=exp.get("start_date"),
                        end_date=exp.get("end_date"),
                        location=exp.get("location"),
                        description=exp.get("description"),
                    )
                )
            except Exception:
                continue

        # From LLM knowledge base
        if not experiences and llm_enrichment.get("experiences"):
            for exp in llm_enrichment["experiences"]:
                try:
                    experiences.append(exp)
                except Exception:
                    continue

        return experiences

    def _extract_education(self, structured: Dict, llm_enrichment: Dict) -> list:
        """Extrait l'éducation"""
        education = (structured.get("education") or []) if structured else []
        if not education and llm_enrichment.get("education"):
            education = llm_enrichment.get("education", [])
        # S'assurer que c'est toujours une liste
        return education if isinstance(education, list) else []

    def _extract_skills(self, structured: Dict, llm_enrichment: Dict) -> list:
        """Extrait les compétences"""
        skills = (structured.get("skills") or []) if structured else []
        if not skills and llm_enrichment.get("skills"):
            skills = llm_enrichment.get("skills", [])
        # S'assurer que c'est toujours une liste
        return skills if isinstance(skills, list) else []

    def _extract_publications(self, news_result: Dict) -> list:
        """Extrait les publications"""
        publications = []
        for art in news_result.get("news_articles", []) or []:
            if art.get("title") and art.get("url"):
                publications.append(f"{art['title']} - {art['url']}")
        for pm in news_result.get("professional_mentions", []) or []:
            if pm.get("source"):
                publications.append(f"Mention - {pm['source']}")
        return publications

    def _extract_speaking(self, company_result: Dict) -> list:
        """Extrait les conférences"""
        speaking = []
        for m in company_result.get("person_mentions", []) or []:
            title = m.get("title") or ""
            if any(
                k in title.lower() for k in ["keynote", "conférence", "talk", "speech"]
            ):
                speaking.append(f"{title} - {m.get('url','')}")
        return speaking

    def _analyze_linkedin_posts(self, li_result: Dict) -> LinkedInAnalysis:
        """Analyse les posts LinkedIn"""
        try:
            li_posts_objs = []
            for p in li_result.get("posts", []) or []:
                try:
                    li_posts_objs.append(
                        LinkedInPost(
                            content=p.get("content", ""),
                            date=p.get("date"),
                            url=p.get("url"),
                        )
                    )
                except Exception:
                    continue

            posts_summary = {
                "summaries": [],
                "recurring_themes": [],
                "overall_tone": None,
                "posting_frequency": None,
            }
            
            if li_posts_objs:
                try:
                    posts_summary = self.llm.summarize_posts([p.dict() for p in li_posts_objs]) or posts_summary
                except Exception as e:
                    print(f"Erreur lors de l'analyse des posts LinkedIn: {e}")

            return LinkedInAnalysis(
                posts=li_posts_objs,
                recurring_themes=posts_summary.get("recurring_themes", []),
                overall_tone=posts_summary.get("overall_tone"),
                posting_frequency=posts_summary.get("posting_frequency"),
            )
        except Exception as e:
            print(f"Erreur dans _analyze_linkedin_posts: {e}")
            return LinkedInAnalysis(
                posts=[],
                recurring_themes=[],
                overall_tone=None,
                posting_frequency=None,
            )

    def _extract_contact_info(
        self, li_result: Dict, company_result: Dict, social_result: Dict
    ) -> ContactInfo:
        """Extrait les informations de contact"""
        return ContactInfo(
            linkedin_url=li_result.get("url"),
            website=company_result.get("company_website"),
            twitter=(social_result.get("twitter", {}) or {}).get("url"),
            github=(social_result.get("github", {}) or {}).get("url"),
            image_url=(company_result.get("person_profile", {}) or {}).get("image_url"),
        )

    def _generate_synthesis(
        self,
        profile: BaseProfile,
        headline: str,
        summary: str,
        experiences: list,
        publications: list,
        linkedin_analysis: LinkedInAnalysis,
        sources_used: list,
        score: int = 0,
    ) -> Dict:
        """Génère la synthèse globale via LLM"""
        return self.llm.global_synthesis(
            {
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "company": profile.company,
                "headline": headline,
                "summary": summary,
                "experiences": [e.dict() for e in experiences],
                "publications": publications,
                "linkedin_posts_count": len(linkedin_analysis.posts),
                "score": score,
            },
            sources_used,
        )

    def _calculate_reliability(self, profile_data: Dict) -> ReliabilityScore:
        """Calcule le score de fiabilité"""
        scoring_result = ReliabilityScorer.calculate_score(
            sources_used=profile_data["sources_used"],
            headline=profile_data["headline"],
            summary=profile_data["summary"],
            experiences=profile_data["experiences"],
            publications=profile_data["publications"],
            posts=profile_data["linkedin_analysis"].posts,
            education=profile_data["education"],
            skills=profile_data["skills"],
            social_profiles={
                "twitter": profile_data["contact_info"].twitter,
                "github": profile_data["contact_info"].github,
            },
        )

        score = scoring_result["score"]

        # Ajuster si LLM enrichment utilisé
        llm_enrichment = profile_data.get("llm_enrichment", {})
        if llm_enrichment.get("_source") == "llm_knowledge_base":
            scoring_result["factors"].append(
                "Données enrichies depuis base de connaissances LLM (octobre 2023 - peut être obsolète)"
            )
            if llm_enrichment.get("confidence") == "low":
                score = max(20, score - 10)

        # LLM justification
        llm_justif = self.llm.justify_reliability(
            {
                "score": score,
                "sources": profile_data["sources_used"],
                "conflicts": [],
                "coverage": "company/news/social/linkedin",
                "factors": scoring_result["factors"],
            }
        )

        synthesis = profile_data.get("synthesis", {})
        base_justification = f"Score de fiabilité: {score}/100. {ReliabilityScorer.get_reliability_level(score)}"
        final_justification = (
            llm_justif.get("justification")
            or synthesis.get("reliability_justification")
            or base_justification
        )

        return ReliabilityScore(
            score=score,
            justification=final_justification,
            factors=scoring_result["factors"],
        )

    def _assemble_profile(
        self,
        data: BaseProfile,
        profile_data: Dict,
        reliability: ReliabilityScore,
    ) -> EnrichedProfile:
        """Assemble le profil enrichi final"""
        synthesis = profile_data.get("synthesis", {})

        reputation = ReputationAnalysis(
            summary=synthesis.get("synthesis", "Profil professionnel"),
            strengths=synthesis.get("strengths", []),
            weak_signals=synthesis.get("weak_signals", []),
        )

        return EnrichedProfile(
            first_name=data.first_name,
            last_name=data.last_name,
            company=data.company,
            headline=profile_data["headline"],
            current_role=profile_data["current_role"],
            summary=profile_data["summary"],
            experiences=profile_data["experiences"],
            linkedin_analysis=profile_data["linkedin_analysis"],
            skills=profile_data["skills"],
            education=profile_data["education"],
            publications=profile_data["publications"],
            speaking_engagements=profile_data["speaking_engagements"],
            contact_info=profile_data["contact_info"],
            reputation=reputation,
            reliability=reliability,
            sources_used=profile_data["sources_used"],
        )
