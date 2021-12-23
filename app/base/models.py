# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin
from sqlalchemy import LargeBinary, Column, Integer, String, Float
import numpy as np
from app import db, login_manager

from app.base.util import hash_pass

class User(db.Model, UserMixin):

    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(LargeBinary)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass( value ) # we need bytes here (not plain str)
                
            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)

class Device(db.Model, UserMixin):
    __tablename__ = 'Device'

    id = Column(Integer, primary_key=True)
    devID = Column(String, unique=True)
    location = Column(String)
    date = Column(String)
    moreInfo = Column(String)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)




class Stuff(db.Model, UserMixin):
    __tablename__ = 'Stuff'
    id = Column(Integer, primary_key=True)
    stuffID = Column(String, unique=True)
    stuffName = Column(String, unique=True)
    email = Column(String, unique=True)
    apartment = Column(String)
    date = Column(String)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)




class SenserData(db.Model, UserMixin):
    __tablename__ = 'SenserData'
    time = Column(Integer, primary_key=True)
    humidity = Column(Float)
    temp = Column(Float)
    windSpeed = Column(Float)
    windDirect = Column(Float)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def to_json(self):
        return {
            'time': self.time,
            'humidity': self.humidity,
            'temp': self.temp,
            'windSpeed': self.windSpeed,
            'windDirect': self.windDirect
        }
    def to_tuple(self):
        return (self.time,self.humidity, self.temp,self.windSpeed, self.windDirect)
    def to_array(self):
        return np.array([self.time,self.humidity, self.temp,self.windSpeed, self.windDirect])



@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    return user if user else None
