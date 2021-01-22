from peewee import *
import datetime

from dataModels.BaseModel import BaseModel


class User(BaseModel):
    name = CharField(max_length=256, unique=True) #Actual user name
    email = CharField(max_length=256, unique=True) #User login name
    password = CharField(max_length=256)
    billingDate = \
        DateTimeField(default=
                        datetime.datetime(
                            datetime.datetime.now().year,#current year
                            datetime.datetime.now().month,#current month
                            5))#todo: should it be day of the month :)
    firstSubscriptionOn = DateTimeField(default=None)
    phone = CharField(max_length=15, unique=True)
    address1 = CharField(max_length=1000)
    address2 = CharField(max_length=1000)
    datacenter_id = IntegerField(default=-1)
    vlan_id = IntegerField(default=-1)
    miscinfo = CharField(max_length=1000)
    region_name = CharField(max_length=256)
    created = DateTimeField(default=datetime.datetime.now)
    modified = DateTimeField(default=datetime.datetime.now)





