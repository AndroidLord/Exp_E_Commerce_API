import jwt
from fastapi import FastAPI, Depends
from tortoise import models
from tortoise.contrib.fastapi import register_tortoise

import config
# Authentication
from authentication import get_hashed_password, verify_access_token, authenticate_user, create_access_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

import models, emailConfig

# signals
from tortoise.signals import post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient

# response classes
from fastapi.responses import HTMLResponse
from fastapi import Request, status, HTTPException

# templates
from fastapi.templating import Jinja2Templates

# Image upload
from fastapi import File, UploadFile
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image

app = FastAPI()

oath2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/login")
async def login(user_credentials: OAuth2PasswordRequestForm = Depends()):
    print("Entered login")

    token = await create_access_token(user_credentials.username, user_credentials.password)

    user = await models.User.get(username=user_credentials.username)

    business = await models.Business.get(owner=user)
    logo = business.logo[1:]
    logo_FullPath = f"http://localhost:8000{logo}"


    return {"access_token": token, "token_type": "bearer", "data": user, "logo": logo_FullPath}


async def get_current_user(token: str = Depends(oath2_scheme)):
    credentials_exceptions = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                           detail=f"Could not validate credentials",
                                           headers={"WWW-Authenticate": "Bearer"})

    return verify_access_token(token, credentials_exceptions)


@post_save(models.User)
async def create_business(
        sender: "Type[models.User]",
        instance: models.User,
        created: bool,
        using_db: "Optional[BaseDBAsyncClient]",
        update_fields: List[str]) -> None:
    print("Entered post_save")

    if created:
        business = await models.Business.create(business_name=instance.username, owner=instance)
        print("Entered create_Business ")
        await models.business_pydantic.from_tortoise_orm(business)
        print(f"Business created for {instance.username}")

        # Send the email
        await emailConfig.send_email([instance.email], instance)


# User Path

@app.post("/users")
async def create_user(user: models.user_pydanticIn):
    print(user.dict(exclude_unset=True))

    print("Entered create_user")

    user_info = user.dict(exclude_unset=True)
    user_info["password"] = get_hashed_password(user_info["password"])
    print("Creating user...")
    user_obj = await models.User.create(**user_info)
    new_user = await models.user_pydanticOut.from_tortoise_orm(user_obj)

    print('User created')
    print(new_user.dict())

    return {
        "status": "ok",
        "data": f"Hello {new_user.username}, thanks for choosing to join us!. Also check your email to verify your "
                f"account."
    }


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/test")
async def root(user: models.User = Depends(get_current_user)):
    user = await user
    return {
        "message": "Hello World",
        "user": user
    }


templates = Jinja2Templates(directory="templates")


@app.get("/verification/", response_class=HTMLResponse)
async def verify_email(request: Request, token: str):
    credits_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    user = await verify_access_token(token, credits_exception)

    if user and not user.is_verified:
        user.is_verified = True
        await user.save()
        return templates.TemplateResponse(
            "verification.html",
            {"request": request, "username": user.username}
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    pass


@app.post("/uploadFile/profile")
async def create_upload_file(file: UploadFile = File(...), user: models.user_pydanticIn = Depends(get_current_user)):
    print("Entered uploadFile")
    print(file.filename)
    print(file.content_type)
    print(file.file)

    user = await user
    print(user.username)

    # Check file extension
    filename = file.filename
    extension = filename.split(".")[1]
    if extension not in ["jpg", "png"]:
        return {"status": "error", "detail": "file extension not allowed"}

    # Save the file
    image_name = f"{secrets.token_hex(8)}_{file.filename}"
    IMAGE_FILEPATH = f"./static/images/{image_name}"
    with open(IMAGE_FILEPATH, "wb") as buffer:
        buffer.write(await file.read())

    # Resize the image
    image = Image.open(IMAGE_FILEPATH)
    image.thumbnail((200, 200))
    image.save(IMAGE_FILEPATH)

    await file.close()

    business = await models.Business.get(owner=user)
    owner = await business.owner

    if owner == user:
        business.logo = IMAGE_FILEPATH
        await business.save()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Update the user
    # user = await models.User.get(username=user.username)
    # user.profile_picture = IMAGE_FILEPATH
    # await user.save()

    return {
        "status": "ok",
        "data": f"Profile picture updated",
        "image_path": IMAGE_FILEPATH
    }


@app.post("/uploadFile/product/{id}")
async def create_upload_file(id: int,
                             file: UploadFile = File(...),
                             user: models.user_pydanticIn = Depends(get_current_user)):
    print("Entered Product uploadFile")
    print(file.filename)
    print(file.content_type)
    print(file.file)

    user = await user
    print(user.username)

    # Check file extension
    filename = file.filename
    extension = filename.split(".")[1]
    if extension not in ["jpg", "png"]:
        return {"status": "error", "detail": "file extension not allowed"}

    # Save the file
    image_name = f"{secrets.token_hex(8)}_{file.filename}"
    IMAGE_FILEPATH = f"./static/images/{image_name}"
    with open(IMAGE_FILEPATH, "wb") as buffer:
        buffer.write(await file.read())

    # Resize the image
    image = Image.open(IMAGE_FILEPATH)
    image.thumbnail((200, 200))
    image.save(IMAGE_FILEPATH)

    await file.close()

    product = await models.Product.get(id=id)
    business = await product.business
    owner = await business.owner

    if owner == user:
        product.product_image = IMAGE_FILEPATH
        await product.save()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "status": "ok",
        "data": f"Product image updated",
        "image_path": IMAGE_FILEPATH
    }


register_tortoise(
    app,
    db_url="sqlite://database.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True, )
