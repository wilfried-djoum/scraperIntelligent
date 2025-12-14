from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BaseProfile(BaseModel):
    """Modèle de base pour un profil utilisateur"""

    first_name: str
    last_name: str
    company: str

    def getFullName(self):
        return f"{self.first_name} {self.last_name}"


class Experience(BaseModel):
    """Modèle pour une expérience professionnelle"""

    title: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    key_achievements: List[str] = Field(default_factory=list)
    is_current: bool = False


class LinkedInPost(BaseModel):
    """Modèle pour un post LinkedIn"""

    content: str
    date: Optional[str] = None
    summary: Optional[str] = None
    themes: List[str] = Field(default_factory=list)
    engagement_level: Optional[str] = None  # "faible", "moyen", "élevé"
    url: Optional[str] = None


class LinkedInAnalysis(BaseModel):
    """Analyse globale des posts LinkedIn"""

    posts: List[LinkedInPost] = Field(default_factory=list)
    recurring_themes: List[str] = Field(default_factory=list)
    expertise_level: Optional[str] = (
        None  # "débutant", "intermédiaire", "expert", "leader d'opinion"
    )
    authority_signals: Optional[str] = None
    overall_tone: Optional[str] = None
    posting_frequency: Optional[str] = None


class ReputationAnalysis(BaseModel):
    """Analyse de la réputation professionnelle"""

    quality_score: Optional[str] = None  # "faible", "moyenne", "élevée", "excellente"
    peer_recognition: Optional[str] = None
    interaction_quality: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    weak_signals: List[str] = Field(default_factory=list)
    summary: Optional[str] = None


class ReliabilityScore(BaseModel):
    """Score de fiabilité du profil"""

    score: int = Field(ge=0, le=100, description="Score de 0 à 100")
    justification: str
    factors: List[str] = Field(default_factory=list)


class ContactInfo(BaseModel):
    """Informations de contact publiques"""

    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter: Optional[str] = None
    website: Optional[str] = None
    github: Optional[str] = None
    image_url: Optional[str] = None


class EnrichedProfile(BaseModel):
    """Profil complet enrichi avec toutes les analyses"""

    # Informations de base
    first_name: str
    last_name: str
    company: Optional[str] = None

    # Profil synthétique
    current_role: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)

    # Parcours professionnel
    experiences: List[Experience] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)

    # Analyse LinkedIn
    linkedin_analysis: Optional[LinkedInAnalysis] = None

    # Réputation professionnelle
    reputation: Optional[ReputationAnalysis] = None

    # Publications et interventions
    publications: List[str] = Field(default_factory=list)
    speaking_engagements: List[str] = Field(default_factory=list)

    # Contacts professionnels publics
    contact_info: Optional[ContactInfo] = None

    # Score de fiabilité
    reliability: Optional[ReliabilityScore] = None

    # Métadonnées
    sources_used: List[str] = Field(default_factory=list)
    scraping_date: Optional[str] = None
    processing_time: Optional[float] = None
