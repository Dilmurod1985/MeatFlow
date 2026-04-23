from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Workshop(Base):
    __tablename__ = "workshops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    inventory = relationship("Inventory", back_populates="workshop", cascade="all, delete-orphan")
    plans = relationship("ProductionPlan", back_populates="workshop", cascade="all, delete-orphan")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    workshop_id = Column(Integer, ForeignKey("workshops.id"), nullable=False)
    item_name = Column(String(200), nullable=False)
    current_stock = Column(Float, nullable=False, default=0.0)
    is_finished = Column(Boolean, nullable=False, default=False)
    # коэффициент выхода (сколько единиц сырья требуется для 1 единицы готовой продукции)
    yield_coeff = Column(Float, nullable=False, default=1.0)

    workshop = relationship("Workshop", back_populates="inventory")


class ProductionPlan(Base):
    __tablename__ = "production_plans"
    __table_args__ = (
        UniqueConstraint("workshop_id", "date", name="uix_workshop_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    workshop_id = Column(Integer, ForeignKey("workshops.id"), nullable=False)
    date = Column(Date, nullable=False)
    # план выхода в тоннах/килограммах (в тех же единицах, что и остатки)
    plan_output = Column(Float, nullable=False, default=0.0)

    workshop = relationship("Workshop", back_populates="plans")


class ProductionLog(Base):
    __tablename__ = "production_log"

    id = Column(Integer, primary_key=True, index=True)
    workshop_id = Column(Integer, ForeignKey("workshops.id"), nullable=False)
    item_name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False)
    timestamp = Column(String(50), nullable=False)

    workshop = relationship("Workshop")


class MeatConsumption(Base):
    __tablename__ = "meat_consumption"

    id = Column(Integer, primary_key=True, index=True)
    workshop_id = Column(Integer, ForeignKey("workshops.id"), nullable=False)
    meat_type = Column(String(100), nullable=False)  # Лахм, Качалка, Куринный Бедро и т.д.
    quantity = Column(Float, nullable=False)  # количество в кг
    date = Column(Date, nullable=False)
    timestamp = Column(String(50), nullable=False)

    workshop = relationship("Workshop")
