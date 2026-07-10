from fastapi import FastAPI

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

app.include_router(router)
mount_admin(app)
