
from sqlalchemy import Column, Integer, String, Text
from database import Base


# Blog table define karna
class Blog(Base):
    # Database mein table ka naam
    __tablename__ = "blogs"

    # Har blog ki unique ID
    id = Column(Integer, primary_key=True, index=True)

    # Blog ka title store hoga
    title = Column(String)

    # Blog ka content store hoga
    content = Column(Text)
