import mongomock
import pytest

from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.registrar.repository import RegistrarRepository
from app.modules.registrar.service import RegistrarService
from app.modules.survey.repository import SurveyRepository
from app.modules.survey.service import SurveyService


@pytest.fixture
def db():
    client = mongomock.MongoClient()
    database = client["lrmis_test"]
    yield database
    client.close()


@pytest.fixture
def audit_service(db):
    return AuditService(AuditRepository(db))


@pytest.fixture
def survey_service(db, audit_service):
    return SurveyService(SurveyRepository(db), audit_service)


@pytest.fixture
def registrar_service(db, audit_service):
    return RegistrarService(RegistrarRepository(db), audit_service)
