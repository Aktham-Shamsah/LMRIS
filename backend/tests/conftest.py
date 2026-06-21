import mongomock
import pytest

from app.modules.applicants.repository import ApplicantRepository
from app.modules.applications.repository import ApplicationRepository
from app.modules.applications.service import ApplicationService
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.registrar.repository import RegistrarRepository
from app.modules.registrar.service import RegistrarService
from app.modules.staff.repository import StaffRepository
from app.modules.staff.service import StaffService
from app.modules.survey.repository import SurveyRepository
from app.modules.survey.service import SurveyService


@pytest.fixture()
def db():
    client = mongomock.MongoClient()
    return client["lrmis_test"]


@pytest.fixture()
def audit(db):
    return AuditService(AuditRepository(db))


@pytest.fixture()
def application_service(db, audit):
    return ApplicationService(ApplicationRepository(db), ApplicantRepository(db), audit)


@pytest.fixture()
def staff_service(db):
    return StaffService(StaffRepository(db))


@pytest.fixture()
def survey_service(db, audit):
    return SurveyService(SurveyRepository(db), audit)


@pytest.fixture()
def registrar_service(db, audit):
    return RegistrarService(RegistrarRepository(db), audit)

