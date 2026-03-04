from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from controllers import auth_controller
from models.user import UserCreate, UserLogin

auth_routes = APIRouter()
security = HTTPBearer()


@auth_routes.post("/register")
async def register(user: UserCreate):
    return await auth_controller.signup_user(user)


@auth_routes.post("/login")
async def login(user: UserLogin):
    return await auth_controller.login_user(user)


@auth_routes.post("/logout")
async def logout():
    return await auth_controller.logout_user()


@auth_routes.get("/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await auth_controller.get_current_user_from_token(credentials.credentials)
