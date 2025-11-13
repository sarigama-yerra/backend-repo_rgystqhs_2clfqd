import os
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Product as ProductSchema

app = FastAPI(title="Clothing Brand API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
    image: Optional[str] = None


def serialize_doc(doc: dict) -> dict:
    d = dict(doc)
    _id = d.pop("_id", None)
    if _id is not None:
        d["id"] = str(_id)
    return d


@app.get("/")
def read_root():
    return {"message": "Clothing Brand Backend is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


@app.get("/api/products")
async def list_products(category: Optional[str] = None, limit: int = 50) -> List[dict]:
    if db is None:
        return []
    filt = {"category": category} if category else {}
    docs = get_documents("product", filt, limit)
    return [serialize_doc(d) for d in docs]


@app.post("/api/products", status_code=201)
async def create_product(product: ProductCreate) -> dict:
    # Validate using schemas.Product for consistency
    _ = ProductSchema(
        title=product.title,
        description=product.description,
        price=product.price,
        category=product.category,
        in_stock=product.in_stock,
    )
    payload: dict = product.model_dump()
    inserted_id = create_document("product", payload)
    return {"id": inserted_id}


@app.post("/api/seed")
async def seed_products() -> dict:
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    count = db["product"].count_documents({})
    if count > 0:
        return {"seeded": False, "message": "Products already exist"}

    demo_items = [
        {
            "title": "Classic Tee - Black",
            "description": "Premium cotton. Tailored fit.",
            "price": 29.0,
            "category": "tops",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1520975922131-c0f3c0b1c1a9?q=80&w=800&auto=format&fit=crop"
        },
        {
            "title": "Oversized Hoodie - Cream",
            "description": "Heavyweight fleece with embroidered logo.",
            "price": 69.0,
            "category": "hoodies",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1520975922131-1b2e?crop=faces&fit=crop&w=800&q=80"
        },
        {
            "title": "Relaxed Fit Jeans",
            "description": "Vintage wash, straight leg.",
            "price": 59.0,
            "category": "bottoms",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=800&auto=format&fit=crop"
        },
        {
            "title": "Utility Jacket - Olive",
            "description": "Water-repellent with multi pockets.",
            "price": 119.0,
            "category": "outerwear",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?q=80&w=800&auto=format&fit=crop"
        },
    ]

    for item in demo_items:
        create_document("product", item)

    return {"seeded": True, "count": len(demo_items)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
