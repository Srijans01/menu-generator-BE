from pydantic import BaseModel

class Dish(BaseModel):
    name: str
    price: float

class Category(BaseModel):
    name: str
    dishes: list[Dish] = []

class Menu(BaseModel):
    id: str = None  # Default to None, will be set on creation
    name: str
    categories: list[Category] = []

class Restaurant(BaseModel):
    name: str
    location: str
    menus: list[Menu] = []
