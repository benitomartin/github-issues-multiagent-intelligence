from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.utils.config import settings


class DBConfig(BaseModel):
    username: str
    password: str
    host: str
    port: int = Field(..., ge=1, le=65535)
    dbname: str
    driver: str = "postgresql+psycopg2"

    def build_url(self) -> str:
        return f"{self.driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.dbname}"


class Base(DeclarativeBase):
    pass


class Issue(Base):  # type: ignore
    __tablename__ = settings.ISSUES_TABLE_NAME
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    owner: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    repo: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str | None] = mapped_column(String(20), nullable=True)
    author: Mapped[str | None] = mapped_column(String(100), nullable=True)
    url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_bug: Mapped[bool] = mapped_column(Boolean, default=False)
    is_feature: Mapped[bool] = mapped_column(Boolean, default=False)

    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="issue", cascade="all, delete-orphan")


class Comment(Base):  # type: ignore
    __tablename__ = settings.COMMENTS_TABLE_NAME
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    comment_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    issue_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("issues.id"), nullable=False)
    author: Mapped[str | None] = mapped_column(String(100), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    issue: Mapped["Issue"] = relationship("Issue", back_populates="comments")
