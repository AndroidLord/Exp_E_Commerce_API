from typing import List

from fastapi import BackgroundTasks, UploadFile
from fastapi import File, Form, Depends, HTTPException, status

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from models import User
from config import settings as sys

from pydantic import BaseModel, EmailStr

# lib for JWT
import jwt

conf = ConnectionConfig(
    MAIL_USERNAME=sys.ADMIN_EMAIL,
    MAIL_PASSWORD=sys.ADMIN_PASSWORD,
    MAIL_FROM=sys.ADMIN_EMAIL,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


class EmailSchema(BaseModel):
    email: List[EmailStr]


async def send_email(email: List, instance: User):
    token_data = {
        "id": instance.id,
        "username": instance.username
    }

    token = jwt.encode(token_data, sys.SECRET_KEY, algorithm="HS256")

    template = f"""
    <!Doctype html>
    <html>
    <head>
        <title>Verify your account</title>
    </head>
    <body>
    
       <div style="display: flex; justify-content: center; align-items: center; flex-direction: column;">
        
        <h3> Account Verification </h3>
        <br> 
        <p> Hello {instance.username}, thanks for choosing to join us!. Please click on the button below to verify 
        your account.</p>
        
        <a style="margin-top: lrem; padding: 1rem; background-color: #4CAF50; color: white; border-radius: 0.5rem;
        text-decoration: none; font-size: 1rem;" href="http://localhost:8000/verification/?token={token}">
        Verify your email
        </a>
        
        <p> If you did not create an account, no further action is required.</p>
        
        </div>
    
    </body>
    </html>
    
    """

    message = MessageSchema(
        subject="Your Shub E_Commerce Account Verification",
        recipients=email,
        body=template,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message=message)
