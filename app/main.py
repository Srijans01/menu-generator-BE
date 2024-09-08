from fastapi import FastAPI
from app.routes import restaurant, menu, category, dish
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Adding CORS Middleware to allow cross-origin requests during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Including routers for different parts of the application
app.include_router(restaurant.router, prefix="/restaurants", tags=["restaurants"])
app.include_router(menu.router, prefix="/menus", tags=["menus"])
app.include_router(category.router, prefix="/categories", tags=["categories"])
app.include_router(dish.router, tags=["dishes"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Restaurant API"}
