from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_categories():
    return {"message": "This is a category route"}

@router.post("/")
async def create_category(name: str):
    return {"message": f"Category {name} created"}
