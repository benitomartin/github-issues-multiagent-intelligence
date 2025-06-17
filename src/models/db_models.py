from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship

from src.utils.config import settings


class Base(DeclarativeBase):
    pass


class Issue(Base):  # type: ignore
    __tablename__ = settings.ISSUES_TABLE_NAME
    id = Column(BigInteger, primary_key=True, index=True)
    owner = Column(String(100), nullable=False, index=True)
    repo = Column(String(100), nullable=False, index=True)
    number = Column(Integer, unique=True, index=True, nullable=False)
    title = Column(String(300), nullable=False)
    body = Column(Text)
    state = Column(String(20))
    author = Column(String(100))
    url = Column(String(300))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_bug = Column(Boolean, default=False)
    is_feature = Column(Boolean, default=False)

    comments = relationship("Comment", back_populates="issue", cascade="all, delete-orphan")


class Comment(Base):  # type: ignore
    __tablename__ = settings.COMMENTS_TABLE_NAME
    id = Column(BigInteger, primary_key=True, index=True)
    comment_id = Column(BigInteger, unique=True, index=True, nullable=False)
    issue_id = Column(BigInteger, ForeignKey("issues.id"), nullable=False)
    author = Column(String(100))
    body = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    issue = relationship("Issue", back_populates="comments")
