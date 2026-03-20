from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import home, users
from db.models import Base,engine

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://localhost:8080",
        "null"  # For file:// protocol
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

app.include_router(home.router)
app.include_router(users.router)

from sqladmin import Admin
from db.admin import UserAdmin, ProfileAdmin, ChannelAdmin, APICredentialsAdmin

admin = Admin(app, engine)

# Register admin models
admin.add_view(UserAdmin)
admin.add_view(ProfileAdmin)
admin.add_view(ChannelAdmin)
admin.add_view(APICredentialsAdmin)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)