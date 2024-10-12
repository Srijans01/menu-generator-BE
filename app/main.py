from fastapi import FastAPI
from app.routes import restaurant, menu, category, dish, ads, brand
from fastapi.middleware.cors import CORSMiddleware
import uvicorn  # Import uvicorn
import os  # Import os for reading environment variables

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
app.include_router(ads.router, prefix="/ads", tags=["ads"])
app.include_router(brand.router, prefix="/brands", tags=["brands"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Restaurant API"}

# This block is only needed for running the app directly from Python (for local development)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Use PORT from the environment or default to 8000
    uvicorn.run(app, host="0.0.0.0", port=port)
