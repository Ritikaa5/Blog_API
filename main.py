
from fastapi import FastAPI, Request, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import engine, SessionLocal
import models, schemas
from auth import token_create, verify_token


# Database ki tables create karna agar pehle se exist nahi karti
models.Base.metadata.create_all(bind=engine)

# FastAPI application create karna
app = FastAPI()


# ---------------- RATE LIMITER SETUP ----------------

# Client ke IP address ke basis par requests count karna
limiter = Limiter(key_func=get_remote_address)

# Limiter ko FastAPI application ke saath connect karna
app.state.limiter = limiter


# Rate limit exceed hone par error handle karna
@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please try again later."
        }
    )


# ---------------- DATABASE DEPENDENCY ----------------

# API ko database session provide karna
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        # Request complete hone par session close karna
        db.close()


# ---------------- LOGIN API ----------------

@app.post("/login")
def login():
    # Demo user ke liye JWT token create karna
    access_token = token_create({"sub": "admin"})

    # Token client ko return karna
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ---------------- HOME API ----------------

@app.get("/")
def home():
    return {
        "message": "Blog API Started"
    }


# ---------------- CREATE BLOG ----------------

# Protected API: valid JWT token required
@app.post("/blogs", response_model=schemas.BlogResponse)
def create_blog(
    blog: schemas.BlogCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    # Request data se naya Blog object banana
    new_blog = models.Blog(
        title=blog.title,
        content=blog.content
    )

    # Object ko database session mein add karna
    db.add(new_blog)

    # Database mein save karna
    db.commit()

    # Database se generated values, jaise ID, refresh karna
    db.refresh(new_blog)

    # Created blog return karna
    return new_blog


# ---------------- PAGINATION + SEARCH ----------------

@app.get("/blogs")
def get_blogs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=5, ge=1, le=100),
    search: str = Query(default=""),
    db: Session = Depends(get_db)
):
    # Database se blogs ki query banana
    query = db.query(models.Blog)

    # Agar search keyword diya hai, toh title aur content dono mein search karna
    if search.strip():
        keyword = f"%{search.strip()}%"

        query = query.filter(
            (models.Blog.title.ilike(keyword)) |
            (models.Blog.content.ilike(keyword))
        )

    # Search ke baad total matching blogs count karna
    total = query.count()

    # Page number se calculate karna ki kitne blogs skip karne hain
    offset = (page - 1) * limit

    # Stable order mein results fetch karna, phir pagination apply karna
    blogs = (
        query
        .order_by(models.Blog.id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Paginated results aur metadata return karna
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": blogs
    }


# ---------------- READ ONE BLOG ----------------

@app.get("/blogs/{id}", response_model=schemas.BlogResponse)
def get_blog(
    id: int,
    db: Session = Depends(get_db)
):
    # ID ke basis par blog find karna
    blog = db.query(models.Blog).filter(
        models.Blog.id == id
    ).first()

    # Blog nahi mila toh 404 error dena
    if not blog:
        raise HTTPException(
            status_code=404,
            detail="Blog not found"
        )

    return blog


# ---------------- UPDATE BLOG ----------------

# Protected API: valid JWT token required
@app.put("/blogs/{id}", response_model=schemas.BlogResponse)
def update_blog(
    id: int,
    blog: schemas.BlogCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    # Existing blog find karna
    existing_blog = db.query(models.Blog).filter(
        models.Blog.id == id
    ).first()

    # Blog nahi mila toh error dena
    if not existing_blog:
        raise HTTPException(
            status_code=404,
            detail="Blog not found"
        )

    # Existing title aur content update karna
    existing_blog.title = blog.title
    existing_blog.content = blog.content

    # Changes database mein save karna
    db.commit()

    # Updated database values refresh karna
    db.refresh(existing_blog)

    return existing_blog


# ---------------- DELETE BLOG ----------------

# Protected API: valid JWT token required
@app.delete("/blogs/{id}")
def delete_blog(
    id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    # ID ke basis par blog find karna
    blog = db.query(models.Blog).filter(
        models.Blog.id == id
    ).first()

    # Blog nahi mila toh 404 error dena
    if not blog:
        raise HTTPException(
            status_code=404,
            detail="Blog not found"
        )

    # Blog delete karna
    db.delete(blog)

    # Deletion database mein save karna
    db.commit()

    # Success response return karna
    return {
        "message": "Blog deleted successfully"
    }


# ---------------- RATE LIMITING API ----------------

# Ek IP address se maximum 5 requests per minute
@app.get("/data")
@limiter.limit("5/minute")
def get_data(request: Request):
    # SlowAPI ke liye request parameter required hai
    return {
        "message": "Success"
    }
