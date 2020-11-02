from typing import Dict, Any

from fastapi import FastAPI, Request, Response, Depends

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from tortoise.contrib.starlette import register_tortoise

from main.models import user_db, User, UserCreate, UserUpdate, UserDB


DATABASE_URL = "sqlite://./test.db"
origins = [
    "*",
    "http://localhost:4200"
]

app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


register_tortoise(app, modules={"modules": ["main.models"]}, db_url=DATABASE_URL)

templates = Jinja2Templates(directory='templates')


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "name": "Bob"})


@app.get("/item/{item_id}")
async def get_item(request: Request, item_id: int):
    return {"item": {
        "item_id": item_id
    }}


from fastapi_users.authentication import JWTAuthentication

SECRET = "SECRET"

auth_backends = []

jwt_authentication = JWTAuthentication(secret=SECRET, lifetime_seconds=3600)

auth_backends.append(jwt_authentication)

from fastapi_users import FastAPIUsers


fastapi_users = FastAPIUsers(
    user_db,
    auth_backends,
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)


@app.post("/auth/jwt/refresh")
async def refresh_jwt(response: Response, user=Depends(fastapi_users.get_current_active_user)):
    return await jwt_authentication.get_login_response(user, response)

# auth routes
app.include_router(
    fastapi_users.get_auth_router(jwt_authentication),
    prefix="/auth/jwt",
    tags=["auth"],
)


# registrant routes
def on_after_register(user: UserDB, request: Request):
    print(f"User {user.id} has registered.")


app.include_router(
    fastapi_users.get_register_router(on_after_register),
    prefix="/auth",
    tags=["auth"],
)


# forgot password rote
def on_after_forgot_password(user: UserDB, token: str, request: Request):
    print(f"User {user.id} has forgot their password. Reset token: {token}")


app.include_router(
    fastapi_users.get_reset_password_router(SECRET, after_forgot_password=on_after_forgot_password),
    prefix="/auth",
    tags=["auth"],
)


# route for managing users
def on_after_update(user: UserDB, updated_user_data: Dict[str, Any], request: Request):
    print(f"User {user.id} has been updated with the following data: {updated_user_data}")


app.include_router(
    fastapi_users.get_users_router(on_after_update),
    prefix="/users",
    tags=["users"],
)
