import os
from OpenOversight.app import create_app, db
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app.run(port=3000, host='0.0.0.0')
