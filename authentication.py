from fastapi.exceptions import HTTPException
from fastapi import status
from passlib.context import CryptContext
import jwt
from config import settings as sys
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hashed_password(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def verify_access_token(token: str, credentials_exceptions):
    try:
        payload = jwt.decode(token, sys.SECRET_KEY, algorithms=["HS256"])
        user = await User.get(id=payload.get("id"))

        if user is None:
            raise credentials_exceptions
        print(f"The type of User ID:{user.id} is: {type(user.id)}")
        token_data = user

    except jwt.PyJWTError:
        raise credentials_exceptions

    return token_data


async def authenticate_user(username: str, password: str):
    user = await User.get(username=username)

    if user and verify_password(plain_password=password, hashed_password=user.password):
        return user

    return False


async def create_access_token(username: str, password: str):

    user = await authenticate_user(username, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token_data = {
        "id": user.id,
        "username": user.username
    }

    token = jwt.encode(token_data, sys.SECRET_KEY, algorithm="HS256")

    return token
