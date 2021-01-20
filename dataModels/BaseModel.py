import peewee as pw
from peewee import Model
# from settings import *
from peewee import *

# app_settings_file_path = os.getcwd() + "/app.settings"
# load_app_config(app_settings_file_path)
db_host = "localhost"
db_port = "3306"
db_name = "minerva"
db_user = "root"
db_pass = "root"

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


