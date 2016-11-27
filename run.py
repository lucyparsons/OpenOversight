import os
from OpenOversight.app import create_app, db
config = os.getenv('FLASK_CONFIG') or 'default'
app = create_app(config)
app.run(port=3000, host='0.0.0.0')
