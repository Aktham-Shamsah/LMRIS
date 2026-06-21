from fastapi import APIRouter, Depends

from app.core.security import require_registrar_role
from app.modules.auth.models import CurrentUser
from app.modules.registrar.models import RegistrarReviewRequest
from app.modules.registrar.service import RegistrarService
from app.shared.responses import ok

router = APIRouter(tags=["Registrar"], dependencies=[Depends(require_registrar_role)])
service = RegistrarService()


@router.patch("/applications/{application_id}/registrar-review")
def registrar_review(application_id: str, payload: RegistrarReviewRequest, user: CurrentUser = Depends(require_registrar_role)):
    payload.registrar_id = user.actor_id or payload.registrar_id
    return ok(service.review(application_id, payload), "Registrar decision recorded.")

