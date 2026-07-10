"""Back-office SQLAdmin : CRUD + file de validation des extractions.

Remplace le rôle de Directus dans vie-publique.sn, sans service supplémentaire.
"""

import secrets

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.config import settings
from app.db import engine
from app.models import Decision, Document, Mandat, Nomination, Personne, Run, Source, Structure


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        user = str(form.get("username", ""))
        password = str(form.get("password", ""))
        ok = secrets.compare_digest(user, settings.admin_user) and secrets.compare_digest(
            password, settings.admin_password
        )
        if ok:
            request.session.update({"user": user})
        return ok

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("user") == settings.admin_user


class SourceAdmin(ModelView, model=Source):
    column_list = [Source.slug, Source.nom, Source.type, Source.cadence, Source.actif]
    icon = "fa-solid fa-database"


class DocumentAdmin(ModelView, model=Document):
    column_list = [
        Document.id,
        Document.source,
        Document.type_doc,
        Document.titre,
        Document.date_publication,
        Document.statut_extraction,
    ]
    column_searchable_list = [Document.titre, Document.url]
    column_default_sort = ("id", True)
    icon = "fa-solid fa-file-lines"


class NominationAdmin(ModelView, model=Nomination):
    name_plural = "Nominations (validation)"
    column_list = [
        Nomination.id,
        Nomination.personne,
        Nomination.poste,
        Nomination.structure,
        Nomination.date_effet,
        Nomination.score_confiance,
        Nomination.statut_validation,
    ]
    column_default_sort = ("id", True)
    icon = "fa-solid fa-user-check"


class DecisionAdmin(ModelView, model=Decision):
    name_plural = "Décisions (validation)"
    column_list = [
        Decision.id,
        Decision.document,
        Decision.ministere,
        Decision.type,
        Decision.objet,
        Decision.score_confiance,
        Decision.statut_validation,
    ]
    column_searchable_list = [Decision.objet, Decision.ministere]
    column_default_sort = ("id", True)
    icon = "fa-solid fa-gavel"


class PersonneAdmin(ModelView, model=Personne):
    column_list = [Personne.id, Personne.nom_complet, Personne.nom_normalise]
    column_searchable_list = [Personne.nom_complet]
    icon = "fa-solid fa-user"


class StructureAdmin(ModelView, model=Structure):
    column_list = [Structure.id, Structure.sigle, Structure.nom, Structure.type]
    column_searchable_list = [Structure.nom, Structure.sigle]
    icon = "fa-solid fa-building-columns"


class MandatAdmin(ModelView, model=Mandat):
    column_list = [
        Mandat.id,
        Mandat.personne,
        Mandat.poste,
        Mandat.structure,
        Mandat.date_debut,
        Mandat.date_fin,
    ]
    icon = "fa-solid fa-id-badge"


class RunAdmin(ModelView, model=Run):
    name_plural = "Runs (journal d'ingestion)"
    column_list = [Run.id, Run.source, Run.debut, Run.fin, Run.statut, Run.nb_nouveaux, Run.nb_vus]
    column_default_sort = ("id", True)
    can_create = False
    can_edit = False
    icon = "fa-solid fa-clock-rotate-left"


def mount_admin(app: FastAPI) -> None:
    admin = Admin(
        app,
        engine,
        title="Faso Civic — Admin",
        authentication_backend=AdminAuth(secret_key=settings.secret_key),
    )
    for view in (
        SourceAdmin,
        DocumentAdmin,
        DecisionAdmin,
        NominationAdmin,
        PersonneAdmin,
        StructureAdmin,
        MandatAdmin,
        RunAdmin,
    ):
        admin.add_view(view)
