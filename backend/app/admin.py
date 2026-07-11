"""Back-office SQLAdmin : CRUD + file de validation des extractions.

Remplace le rôle de Directus dans vie-publique.sn, sans service supplémentaire.
"""

import secrets

from fastapi import FastAPI
from sqladmin import Admin, ModelView, action
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import update
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.config import settings
from app.db import SessionLocal, engine
from app.models import (
    BudgetExercice,
    Decision,
    Document,
    EngagementFinancier,
    Mandat,
    Nomination,
    Personne,
    Run,
    Source,
    Structure,
)


def _pks(request: Request) -> list[int]:
    brut = request.query_params.get("pks", "")
    return [int(pk) for pk in brut.split(",") if pk]


def _retour(request: Request, defaut: str) -> RedirectResponse:
    return RedirectResponse(request.headers.get("Referer", defaut), status_code=302)


class ValidationActionsMixin:
    """Actions de validation en masse sur les entités extraites (cases à cocher)."""

    modele: type  # Decision ou Nomination

    @action(
        name="valider",
        label="✓ Valider la sélection",
        confirmation_message="Valider les éléments sélectionnés ? Ils deviendront publics via l'API.",
        add_in_detail=True,
        add_in_list=True,
    )
    async def valider(self, request: Request):
        with SessionLocal() as db:
            db.execute(
                update(self.modele)
                .where(self.modele.id.in_(_pks(request)))
                .values(statut_validation="valide")
            )
            db.commit()
        return _retour(request, request.url_for("admin:list", identity=self.identity))

    @action(
        name="rejeter",
        label="✗ Rejeter la sélection",
        confirmation_message="Rejeter les éléments sélectionnés ?",
        add_in_detail=True,
        add_in_list=True,
    )
    async def rejeter(self, request: Request):
        with SessionLocal() as db:
            db.execute(
                update(self.modele)
                .where(self.modele.id.in_(_pks(request)))
                .values(statut_validation="rejete")
            )
            db.commit()
        return _retour(request, request.url_for("admin:list", identity=self.identity))


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
    page_size = 100
    icon = "fa-solid fa-file-lines"

    @action(
        name="valider_contenu",
        label="✓ Valider décisions + nominations de ces CR",
        confirmation_message=(
            "Valider TOUTES les décisions et nominations extraites des documents "
            "sélectionnés ? Elles deviendront publiques via l'API."
        ),
        add_in_detail=True,
        add_in_list=True,
    )
    async def valider_contenu(self, request: Request):
        pks = _pks(request)
        with SessionLocal() as db:
            for modele in (Decision, Nomination):
                db.execute(
                    update(modele)
                    .where(
                        modele.document_id.in_(pks),
                        modele.statut_validation == "a_valider",
                    )
                    .values(statut_validation="valide")
                )
            db.commit()
        return _retour(request, request.url_for("admin:list", identity=self.identity))


class NominationAdmin(ValidationActionsMixin, ModelView, model=Nomination):
    modele = Nomination
    name_plural = "Nominations (validation)"
    page_size = 100
    column_sortable_list = [Nomination.id, Nomination.statut_validation, Nomination.score_confiance]
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


class DecisionAdmin(ValidationActionsMixin, ModelView, model=Decision):
    modele = Decision
    name_plural = "Décisions (validation)"
    page_size = 100
    column_sortable_list = [Decision.id, Decision.type, Decision.statut_validation]
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


class EngagementAdmin(ValidationActionsMixin, ModelView, model=EngagementFinancier):
    modele = EngagementFinancier
    name_plural = "Engagements financiers (validation)"
    page_size = 100
    column_sortable_list = [
        EngagementFinancier.id,
        EngagementFinancier.montant_fcfa,
        EngagementFinancier.statut_validation,
    ]
    column_list = [
        EngagementFinancier.id,
        EngagementFinancier.document,
        EngagementFinancier.type,
        EngagementFinancier.objet,
        EngagementFinancier.beneficiaire,
        EngagementFinancier.montant_fcfa,
        EngagementFinancier.score_confiance,
        EngagementFinancier.statut_validation,
    ]
    column_searchable_list = [EngagementFinancier.objet, EngagementFinancier.beneficiaire]
    column_default_sort = ("montant_fcfa", True)
    icon = "fa-solid fa-coins"


class BudgetAdmin(ValidationActionsMixin, ModelView, model=BudgetExercice):
    modele = BudgetExercice
    name_plural = "Budgets d'exercice (validation)"
    column_list = [
        BudgetExercice.id,
        BudgetExercice.exercice,
        BudgetExercice.type_loi,
        BudgetExercice.recettes_fcfa,
        BudgetExercice.depenses_fcfa,
        BudgetExercice.score_confiance,
        BudgetExercice.statut_validation,
    ]
    column_default_sort = ("exercice", True)
    icon = "fa-solid fa-scale-balanced"


class PersonneAdmin(ModelView, model=Personne):
    column_list = [Personne.id, Personne.nom_complet, Personne.nom_normalise]
    column_searchable_list = [Personne.nom_complet]
    icon = "fa-solid fa-user"


class StructureAdmin(ModelView, model=Structure):
    column_list = [Structure.id, Structure.sigle, Structure.nom, Structure.type, Structure.canonique]
    column_searchable_list = [Structure.nom, Structure.sigle]
    form_columns = [Structure.nom, Structure.sigle, Structure.type, Structure.canonique]
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
        EngagementAdmin,
        BudgetAdmin,
        PersonneAdmin,
        StructureAdmin,
        MandatAdmin,
        RunAdmin,
    ):
        admin.add_view(view)
