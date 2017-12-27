import sys
import datetime
from sqlalchemy.sql import func
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Users(Base):
    __tablename__ = 'user'
    username = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'username': self.username,
            'id': self.id,
            'email': self.email,
            'picture': self.picture
        }


class Categories(Base):
    __tablename__ = 'catagories'
    name = Column(String(80), nullable=False, unique=True)
    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey(Users.id))
    creator = relationship(
                        Users,
                        single_parent=True,
                        cascade="all, delete-orphan")

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id
        }


class Items(Base):
    __tablename__ = 'items'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    time_created = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey(Users.id))
    owner = relationship(Users, cascade="all, delete-orphan")

    category_type = Column(String(80), ForeignKey(Categories.name))
    category = relationship(Categories,
                            single_parent=True,
                            cascade="all, delete-orphan")

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'time_created': self.time_created
        }

engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
