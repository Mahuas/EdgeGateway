# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""



from flask_migrate import Migrate
from os import environ
import sys

from config import config_dict
from app import create_app, db, socketio
from app.base.models import SenserData
get_config_mode = environ.get('APPSEED_CONFIG_MODE', 'Debug')


try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    sys.exit('Error: Invalid APPSEED_CONFIG_MODE environment variable entry.')



app = create_app(config_mode)
app.app_context().push()
Migrate(app, db)




def add_senserdata(res):
    with app.app_context():
        sensordata = SenserData(**res)
        db.session.add(sensordata)
        db.session.commit()



if __name__ == "__main__":
    socketio.run(app,host='0.0.0.0',debug=False)
