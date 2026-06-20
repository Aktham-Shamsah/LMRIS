from fastapi import APIRouter, Query
from schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from schemas.common import APIResponse, PaginationParams
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])
_svc = UserService()


@router.post("", response_model=APIResponse[UserResponse], status_code=201,
             summary="Register a new user")
def create_user(payload: UserCreate):
    return APIResponse(data=_svc.create(payload), message="User created.")


@router.get("", response_model=APIResponse[UserListResponse],
            summary="List all users with pagination")
def list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    params = PaginationParams(page=page, limit=limit)
    items, total = _svc.list(skip=params.skip, limit=params.limit)
    return APIResponse(
        data=UserListResponse(total=total, page=page, limit=limit, items=items)
    )


@router.get("/{user_id}", response_model=APIResponse[UserResponse],
            summary="Get a user by ID")
def get_user(user_id: str):
    return APIResponse(data=_svc.get(user_id))


@router.patch("/{user_id}", response_model=APIResponse[UserResponse],
              summary="Partially update a user")
def update_user(user_id: str, payload: UserUpdate):
    return APIResponse(data=_svc.update(user_id, payload), message="User updated.")


@router.delete("/{user_id}", response_model=APIResponse[None],
               summary="Delete a user")
def delete_user(user_id: str):
    _svc.delete(user_id)
    return APIResponse(message="User deleted.")
