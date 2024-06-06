from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS

from models import init_db
from routes.delivery import delivery_bp
from routes.sensor import sensor_bp


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Register Blueprints
app.register_blueprint(delivery_bp)
app.register_blueprint(sensor_bp)

# Initialize the database
init_db(app)

from tasks import clear_old_deliveries
scheduler = BackgroundScheduler()
scheduler.add_job(func=clear_old_deliveries, trigger="interval", minutes=5)
scheduler.start()


if __name__ == '__main__':
    app.run(port=3000)
