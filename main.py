"""
ScraperIntelligent - API de profiling professionnel
Point d'entrée principal de l'application
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.models.profile import BaseProfile
from src.services.profile_orchestrator import ProfileOrchestrator

app = FastAPI(
    title="ScraperIntelligent",
    description="API de profiling professionnel intelligent avec LLM",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Initialize orchestrator
orchestrator = ProfileOrchestrator()


@app.get("/")
def home():
    """Endpoint de bienvenue"""
    return {
        "message": "Bienvenue sur ScraperIntelligent API",
        "version": "1.0.0",
        "endpoints": {
            "profiling": "/profiling/",
            "docs": "/docs",
        },
    }


@app.post("/profiling/")
async def profiling(data: BaseProfile):
    """
    Endpoint principal de profiling
    
    Args:
        data: BaseProfile avec first_name, last_name, company
        
    Returns:
        Dict avec debug info et profil enrichi complet
    """
    result = await orchestrator.create_profile(data)
    return result


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
