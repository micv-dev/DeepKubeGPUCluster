import peewee as pw
from peewee import *

from common import ReadConfig

config = ReadConfig.getConfig()
db_host = config.get("database","database.host")
db_port = config.get("database","database.port")
db_name = config.get("database","database.db")
db_user = config.get("database","database.user")
db_pass = config.get("database","database.password")

db = pw.MySQLDatabase(
    db_name, user=db_user,
    password=db_pass,
    host=db_host
)
db.connect(reuse_if_open=True)
class BaseModel(Model):
    """A base model that will use our MySQL database"""
    class Meta:
        database = db


