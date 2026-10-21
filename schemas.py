
from pydantic import BaseModel


# Input Schema: client se aane wale data ko validate karta hai
class BlogCreate(BaseModel):
    title: str
    content: str


# Output Schema: API response ka format define karta hai
class BlogResponse(BaseModel):
    id: int
    title: str
    content: str

    # SQLAlchemy model ke object se data read karne deta hai
    class Config:
        from_attributes = True
