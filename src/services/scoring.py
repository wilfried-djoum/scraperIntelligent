"""
Service de calcul du score de fiabilité d'un profil.
Score sur 100 avec justification détaillée.
"""

from typing import Dict, List, Any


class ReliabilityScorer:
    """Calcule le score de fiabilité d'un profil sur 100."""

    @staticmethod
    def calculate_score(
        sources_used: List[str],
        headline: str = None,
        summary: str = None,
        experiences: List[Any] = None,
        publications: List[str] = None,
        posts: List[Any] = None,
        education: List[str] = None,
        skills: List[str] = None,
        social_profiles: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Calcule le score de fiabilité sur 100 et génère les facteurs détaillés.

        Critères:
        - Sources multiples: +10 par source (max 4 sources = +40)
        - Complétude des champs:
          * headline: +8
          * summary: +10
          * experiences: +12
          * publications: +8
          * posts: +8
          * education: +6
          * skills: +4
          * social_profiles: +4
        - Score de base: 0
        - Score max: 100

        Returns:
            Dict avec score, factors (liste des éléments évalués), breakdown (détail par critère)
        """
        experiences = experiences or []
        publications = publications or []
        posts = posts or []
        education = education or []
        skills = skills or []
        social_profiles = social_profiles or {}

        score = 0
        factors = []
        breakdown = {}

        # Sources multiples (max 40 points)
        source_score = min(10 * len(sources_used), 40)
        score += source_score
        breakdown["sources"] = source_score
        if sources_used:
            factors.append(
                f"{len(sources_used)} source(s) vérifiée(s): {', '.join(sources_used)}"
            )

        # Complétude des champs (max 60 points)
        if headline:
            score += 8
            breakdown["headline"] = 8
            factors.append("Titre professionnel présent")

        if summary and len(summary) > 100:
            score += 10
            breakdown["summary"] = 10
            factors.append("Biographie complète")
        elif summary:
            score += 5
            breakdown["summary"] = 5
            factors.append("Biographie partielle")

        if experiences and len(experiences) > 0:
            exp_score = min(4 * len(experiences), 12)
            score += exp_score
            breakdown["experiences"] = exp_score
            factors.append(f"{len(experiences)} expérience(s) professionnelle(s)")

        if publications and len(publications) > 0:
            pub_score = min(2 * len(publications), 8)
            score += pub_score
            breakdown["publications"] = pub_score
            factors.append(f"{len(publications)} publication(s)/mention(s) média")

        if posts and len(posts) > 0:
            post_score = min(2 * len(posts), 8)
            score += post_score
            breakdown["posts"] = post_score
            factors.append(f"{len(posts)} post(s) LinkedIn analysé(s)")

        if education and len(education) > 0:
            edu_score = min(3 * len(education), 6)
            score += edu_score
            breakdown["education"] = edu_score
            factors.append(f"{len(education)} formation(s)")

        if skills and len(skills) >= 3:
            score += 4
            breakdown["skills"] = 4
            factors.append(f"{len(skills)} compétences identifiées")

        if social_profiles and len([v for v in social_profiles.values() if v]) > 0:
            social_count = len([v for v in social_profiles.values() if v])
            social_score = min(2 * social_count, 4)
            score += social_score
            breakdown["social"] = social_score
            factors.append(f"{social_count} profil(s) social/professionnel")

        # Limiter entre 0 et 100
        score = max(0, min(100, score))

        return {
            "score": score,
            "factors": factors,
            "breakdown": breakdown,
        }

    @staticmethod
    def get_reliability_level(score: int) -> str:
        """Retourne le niveau de fiabilité textuel selon le score."""
        if score >= 85:
            return "Excellent - Profil très fiable avec sources multiples et données complètes"
        elif score >= 70:
            return "Bon - Profil fiable avec informations vérifiées"
        elif score >= 50:
            return "Moyen - Profil partiellement vérifié, données limitées"
        elif score >= 30:
            return "Faible - Profil incomplet avec peu de sources"
        else:
            return "Très faible - Informations insuffisantes pour évaluation"
