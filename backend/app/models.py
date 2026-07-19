import datetime as dt

from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey


from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(String, unique=True, index=True, nullable=True)
    github_username = Column(String, nullable=True)
    github_access_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
class Activity(Base):
    """A single logged unit of practice, from any source."""
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    source = Column(String)          # "github" | "leetcode" | "manual"
    activity_type = Column(String)   # e.g. "commit", "solve", "revision"
    label = Column(String, nullable=True)   # repo name / problem name
    occurred_on = Column(Date, index=True)  # the day this counts toward
    created_at = Column(DateTime, default=dt.datetime.utcnow)