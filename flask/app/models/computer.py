from app.extensions import db
from sqlalchemy import func
from sqlalchemy.orm import relationship

class Computer(db.Model):
    __tablename__ = "computers"

    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=True, index=True)

    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    room_number = db.Column(db.String(20), nullable=True)
    number_in_room = db.Column(db.Integer, nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    building = relationship("Building")
    department = relationship("Department")
    print_events = relationship("PrintEvent", back_populates="computer")
