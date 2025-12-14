from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.models.profile import BaseProfile, EnrichedProfile, LinkedInAnalysis, LinkedInPost, ReputationAnalysis, ContactInfo, ReliabilityScore, Experience
from src.services.sources.linkedin import LinkedInScraper
from src.services.sources.company import CompanyScraper
from src.services.sources.news import NewsScraper
from src.services.sources.social import SocialScraper
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="src/static"), name="static")

items = {}


@app.get("/")
def home():
    return {"Grettings": "Salut tout le monde!"}


@app.post("/profiling/")
async def profiling(data: BaseProfile):
    start = time.time()

    linkedin = LinkedInScraper()
    company = CompanyScraper()
    news = NewsScraper()
    social = SocialScraper()

    # Launch scrapers
    li_result = await linkedin.scrape(data)
    company_result = await company.scrape(data)
    news_result = await news.scrape(data)
    social_result = await social.scrape(data)

    # Build profile
    sources_used = []
    if li_result.get("url"):
        sources_used.append("linkedin")
    if company_result.get("company_website"):
        sources_used.append("company")
    if news_result.get("total_mentions"):
        sources_used.append("news")
    if social_result:
        sources_used.append("social")

    # Headline/Summary heuristics from company page or LinkedIn
    headline = None
    summary = None
    if company_result.get("company_info", {}).get("full_content"):
        content = company_result["company_info"]["full_content"]
        # simple extraction: first sentence mentioning the person
        full_name = data.getFullName()
        for para in content.split("\n\n"):
            if full_name.lower() in para.lower():
                summary = para.strip()[:400]
                break
    # Fallback: bio from company person_profile
    if not summary and (company_result.get("person_profile", {}) or {}).get("bio"):
        summary = (company_result.get("person_profile", {}) or {}).get("bio")
    if not summary and li_result.get("profile", {}).get("about"):
        summary = li_result["profile"]["about"]

    # Publications from news results
    publications = []
    for art in news_result.get("news_articles", []) or []:
        if art.get("title") and art.get("url"):
            publications.append(f"{art['title']} - {art['url']}")
    for pm in news_result.get("professional_mentions", []) or []:
        if pm.get("source"):
            publications.append(f"Mention - {pm['source']}")

    # Speaking engagements: naive from company site mentions
    speaking = []
    for m in company_result.get("person_mentions", []) or []:
        title = m.get("title") or ""
        if any(k in title.lower() for k in ["keynote", "conférence", "talk", "speech"]):
            speaking.append(f"{title} - {m.get('url','')}")

    # LinkedIn posts
    li_posts_objs = []
    for p in li_result.get("posts", []) or []:
        li_posts_objs.append(
            LinkedInPost(
                content=p.get("content", ""),
                date=p.get("date"),
                url=p.get("url"),
            )
        )
    linkedin_analysis = LinkedInAnalysis(posts=li_posts_objs)

    # Contact info
    contact = ContactInfo(
        linkedin_url=li_result.get("url"),
        website=company_result.get("company_website"),
        twitter=(social_result.get("twitter", {}) or {}).get("url"),
        github=(social_result.get("github", {}) or {}).get("url"),
        image_url=(company_result.get("person_profile", {}) or {}).get("image_url"),
    )

    # Current role from company person_profile
    current_role = (company_result.get("person_profile", {}) or {}).get("role")

    # Experiences from company person_profile
    experiences = []
    for exp in (company_result.get("person_profile", {}) or {}).get("experiences", []) or []:
        try:
            experiences.append(Experience(title=exp.get("title") or "", company=data.company, description=exp.get("description")))
        except Exception:
            continue

    reliability = ReliabilityScore(
        score=70 if sources_used else 40,
        justification="Profil basé sur sources multiples (entreprise, news, social, LinkedIn).",
        factors=sources_used,
    )

    profile_obj = EnrichedProfile(
        first_name=data.first_name,
        last_name=data.last_name,
        company=data.company,
        headline=headline,
        current_role=current_role,
        summary=summary,
        experiences=experiences,
        linkedin_analysis=linkedin_analysis,
        publications=publications,
        speaking_engagements=speaking,
        contact_info=contact,
        reliability=reliability,
        sources_used=sources_used,
        scraping_date=time.strftime("%Y-%m-%d"),
        processing_time=round(time.time() - start, 2),
    )

    debug = {
        "input": data.dict(),
        "linkedin_found": li_result.get("url"),
        "company_website": company_result.get("company_website"),
        "news_counts": {
            "articles": len(news_result.get("news_articles", []) or []),
            "pro_mentions": len(news_result.get("professional_mentions", []) or []),
        },
        "social": social_result,
    }

    return {"debug": debug, "profile": profile_obj.dict()}
