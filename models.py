from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()


def init_db(app):
    app.config.from_object('config.Config')
    db.init_app(app)
    with app.app_context():
        # db.drop_all()  # This will drop all tables. Remove this line in production.
        db.create_all()
        deliveries = Delivery.query.all()
        for delivery in deliveries:
            if delivery.contract_address != Config.CONTRACT_ADDRESS:
                db.session.delete(delivery)

        db.session.commit()


class Delivery(db.Model):
    deliveryId = db.Column(db.String, primary_key=True)
    status = db.Column(db.String)
    min_temp = db.Column(db.Float)
    max_temp = db.Column(db.Float)
    min_humidity = db.Column(db.Float)
    max_humidity = db.Column(db.Float)
    is_hidden = db.Column(db.Boolean, default=False)
    sensor_data = db.relationship('SensorData', backref='delivery', lazy=True, cascade="all, delete")
    contract_address = db.Column(db.String)


class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deliveryId = db.Column(db.String, db.ForeignKey('delivery.deliveryId', ondelete="CASCADE"), nullable=False)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    timestamp = db.Column(db.Integer)
