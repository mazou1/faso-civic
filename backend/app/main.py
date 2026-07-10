from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin import mount_admin
from app.api.routes import router

app = FastAPI(
    title="Plateforme civique Burkina Faso",
    description=(
        "Agrégation d'informations publiques officielles burkinabè : journal officiel, "
        "conseil des ministres, nominations, budget. Chaque donnée est liée à son document source."
    ),
    version="0.1.0",
)

# API publique en lecture : ouverte à tous les fronts (esprit open data)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)
mount_admin(app)
