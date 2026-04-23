from pydantic import BaseModel
from typing import Optional
from datetime import date


class ReceiveRequest(BaseModel):
    workshop_id: int
    item_name: str
    quantity: float


class SetPlanRequest(BaseModel):
    workshop_id: int
    date: date
    plan_output: float


class InventoryResponse(BaseModel):
    item_name: str
    current_stock: float
    is_finished: bool
    yield_coeff: float


class WorkshopStatus(BaseModel):
    workshop_id: int
    workshop_name: str
    inventory: list[InventoryResponse]
    plan_output: Optional[float] = 0.0
    need_to_produce: Optional[float] = 0.0
    produced_today: Optional[float] = 0.0
    load_percent: Optional[float] = 0.0


class MeatConsumptionRequest(BaseModel):
    workshop_id: int
    meat_type: str
    quantity: float


class MeatConsumptionResponse(BaseModel):
    id: int
    workshop_id: int
    workshop_name: str
    meat_type: str
    quantity: float
    date: str
    timestamp: str
