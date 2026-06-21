from fastapi import HTTPException, status
from repositories.user_repository import UserRepository
from models.user import UserModel
from schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self) -> None:
        self._repo = UserRepository()

    def create(self, payload: UserCreate) -> dict:
        if self._repo.get_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{payload.email}' is already registered.",
            )
        doc = UserModel.new(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            role=payload.role,
        )
        return self._repo.create(doc)

    def get(self, user_id: str) -> dict:
        user = self._repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user

    def list(self, skip: int, limit: int) -> tuple[list[dict], int]:
        return self._repo.list(skip=skip, limit=limit)

    def update(self, user_id: str, payload: UserUpdate) -> dict:
        self.get(user_id)
        updates = payload.model_dump(exclude_none=True)
        updated = self._repo.update(user_id, updates)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return updated

    def delete(self, user_id: str) -> None:
        self.get(user_id)
        if not self._repo.delete(user_id):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Delete failed.")
