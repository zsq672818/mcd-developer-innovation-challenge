"""SQLAlchemy 声明式基类：后续数据模型继承 Base（阶段 1 落地核心数据模型）。"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
