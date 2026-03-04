from fastapi import HTTPException
from config.mongodb import get_db
from models.user import UserCreate, UserLogin, UserInDB
from utils.util import hash_password, verify_password, create_access_token
from bson import ObjectId
import datetime

db = get_db()
users_collection = db.users


async def signup_user(user_data: UserCreate):
    if users_collection.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = hash_password(user_data.password)
    new_user = {
        "name": user_data.name,
        "email": user_data.email,
        "hashed_password": hashed_pwd,
        "created_at": datetime.datetime.utcnow(),
    }

    result = users_collection.insert_one(new_user)
    user_id = str(result.inserted_id)

    access_token = create_access_token(
        data={"sub": user_data.email, "id": user_id, "name": user_data.name}
    )

    return {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "access_token": access_token,
        "token_type": "bearer",
        "message": "User registered successfully",
    }


async def login_user(login_data: UserLogin):
    user = users_collection.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    access_token = create_access_token(
        data={"sub": user["email"], "id": str(user["_id"]), "name": user["name"]}
    )

    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Login successful",
    }


async def logout_user():
    return {"message": "Logged out successfully"}


async def get_current_user_from_token(token: str):
    from utils.util import verify_token

    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token or session expired")

    email = payload.get("sub")
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}
