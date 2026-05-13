from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def init_db(app):
    db.init_app(app)
    with app.app_context():
        import models  # noqa: F401 - ensure all models are registered
        db.create_all()
