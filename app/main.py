from fastapi import FastAPI, Depends, HTTPException, Response
from typing import Optional
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date, datetime
import io
import csv

from .database import SessionLocal, init_db
from . import models, schemas

# Initialize database (create tables)
init_db()

app = FastAPI(title="MeatFlow MVP")

# Serve static frontend
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# CORS for tablets and network devices
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/panel")
async def read_panel():
    return FileResponse('app/static/index.html')


@app.get("/")
async def read_index():
    return FileResponse('app/static/dashboard.html')


# Dependency: provide a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DEFAULT_WORKSHOPS = ["Филе", "Котлеты", "Разделка", "Фарш", "Шпажирование"]


def ensure_workshops(db: Session):
    existing = db.query(models.Workshop).count()
    if existing == 0:
        for name in DEFAULT_WORKSHOPS:
            db.add(models.Workshop(name=name))
        db.commit()
    # function ensures default workshops exist; no logging here


@app.on_event("startup")
def on_startup():
    # ensure default workshops exist on startup
    db = SessionLocal()
    try:
        ensure_workshops(db)
    finally:
        db.close()


@app.post("/receive")
def receive(req: schemas.ReceiveRequest, db: Session = Depends(get_db)):
    workshop = db.query(models.Workshop).filter(models.Workshop.id == req.workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")

    inv = (
        db.query(models.Inventory)
        .filter(models.Inventory.workshop_id == req.workshop_id)
        .filter(models.Inventory.item_name == req.item_name)
        .first()
    )
    if not inv:
        inv = models.Inventory(
            workshop_id=req.workshop_id,
            item_name=req.item_name,
            current_stock=req.quantity,
            is_finished=False,
            yield_coeff=1.0,
        )
        db.add(inv)
    else:
        inv.current_stock += req.quantity
    db.commit()
    return {"status": "ok", "workshop_id": req.workshop_id, "item": req.item_name, "new_stock": inv.current_stock}


@app.get("/stock/{workshop_id}", response_model=schemas.WorkshopStatus)
def stock(workshop_id: int, db: Session = Depends(get_db)):
    # ensure workshops exist
    ensure_workshops(db)

    workshop = db.query(models.Workshop).filter(models.Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")

    today = date.today()
    plan = (
        db.query(models.ProductionPlan)
        .filter(models.ProductionPlan.workshop_id == workshop_id)
        .filter(models.ProductionPlan.date == today)
        .first()
    )
    plan_output = plan.plan_output if plan else 0.0

    invs = (
        db.query(models.Inventory)
        .filter(models.Inventory.workshop_id == workshop_id)
        .all()
    )

    inventory_resp = [
        schemas.InventoryResponse(
            item_name=i.item_name,
            current_stock=i.current_stock,
            is_finished=i.is_finished,
            yield_coeff=i.yield_coeff,
        )
        for i in invs
    ]

    finished_stock = sum(i.current_stock for i in invs if i.is_finished)
    need_to_produce = max(0.0, plan_output - finished_stock)
    produced = finished_stock
    load_percent = (produced / plan_output * 100.0) if plan_output and plan_output > 0 else 0.0

    return schemas.WorkshopStatus(
        workshop_id=workshop.id,
        workshop_name=workshop.name,
        inventory=inventory_resp,
        plan_output=plan_output,
        need_to_produce=need_to_produce,
        produced_today=produced,
        load_percent=round(load_percent, 2),
    )


@app.post("/set-plan")
def set_plan(req: schemas.SetPlanRequest, db: Session = Depends(get_db)):
    ensure_workshops(db)
    workshop = db.query(models.Workshop).filter(models.Workshop.id == req.workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")

    plan = (
        db.query(models.ProductionPlan)
        .filter(models.ProductionPlan.workshop_id == req.workshop_id)
        .filter(models.ProductionPlan.date == req.date)
        .first()
    )
    if not plan:
        plan = models.ProductionPlan(workshop_id=req.workshop_id, date=req.date, plan_output=req.plan_output)
        db.add(plan)
    else:
        plan.plan_output = req.plan_output
    db.commit()

    # compute produced today and load percent to return immediate status
    invs = (
        db.query(models.Inventory)
        .filter(models.Inventory.workshop_id == req.workshop_id)
        .all()
    )
    produced = sum(i.current_stock for i in invs if i.is_finished)
    plan_output = req.plan_output
    load_percent = (produced / plan_output * 100.0) if plan_output and plan_output > 0 else 0.0
    return {"status": "ok", "workshop_id": req.workshop_id, "date": str(req.date), "plan_output": req.plan_output, "produced_today": produced, "load_percent": load_percent}


@app.post("/release/{workshop_id}")
def release(workshop_id: int, amount: float, db: Session = Depends(get_db)):
    workshop = db.query(models.Workshop).filter(models.Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")

    finished_item = (
        db.query(models.Inventory)
        .filter(models.Inventory.workshop_id == workshop_id)
        .filter(models.Inventory.is_finished == True)
        .first()
    )
    if not finished_item:
        finished_item = models.Inventory(
            workshop_id=workshop_id,
            item_name=f"{workshop.name} - Готовая продукция",
            current_stock=0.0,
            is_finished=True,
            yield_coeff=1.0,
        )
        db.add(finished_item)

    finished_item.current_stock += amount

    raw_items = (
        db.query(models.Inventory)
        .filter(models.Inventory.workshop_id == workshop_id)
        .filter(models.Inventory.is_finished == False)
        .all()
    )
    for raw in raw_items:
        to_consume = min(raw.current_stock, amount * raw.yield_coeff)
        raw.current_stock -= to_consume

    db.commit()

    # return updated production and load
    today = date.today()
    plan = (
        db.query(models.ProductionPlan)
        .filter(models.ProductionPlan.workshop_id == workshop_id)
        .filter(models.ProductionPlan.date == today)
        .first()
    )
    plan_output = plan.plan_output if plan else 0.0
    invs = (
        db.query(models.Inventory)
        .filter(models.Inventory.workshop_id == workshop_id)
        .all()
    )
    produced = sum(i.current_stock for i in invs if i.is_finished)
    load_percent = (produced / plan_output * 100.0) if plan_output and plan_output > 0 else 0.0
    return {"status": "ok", "workshop_id": workshop_id, "finished_stock": finished_item.current_stock, "produced_today": produced, "plan_output": plan_output, "load_percent": load_percent}


@app.post("/clear-workshop/{workshop_id}")
def clear_workshop(workshop_id: int, db: Session = Depends(get_db)):
    workshop = db.query(models.Workshop).filter(models.Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    # Clear all inventory for this workshop
    db.query(models.Inventory).filter(models.Inventory.workshop_id == workshop_id).delete()
    
    # Clear today's plan for this workshop
    today = date.today()
    plan = db.query(models.ProductionPlan).filter(
        models.ProductionPlan.workshop_id == workshop_id,
        models.ProductionPlan.date == today
    ).first()
    if plan:
        db.delete(plan)
    
    db.commit()
    return {"status": "ok", "message": "All workshop data cleared"}


@app.get("/status_all")
def status_all(db: Session = Depends(get_db)):
    ensure_workshops(db)
    today = date.today()
    result = []
    workshops = db.query(models.Workshop).all()
    for w in workshops:
        plan = (
            db.query(models.ProductionPlan)
            .filter(models.ProductionPlan.workshop_id == w.id)
            .filter(models.ProductionPlan.date == today)
            .first()
        )
        plan_output = plan.plan_output if plan else 0.0
        invs = (
            db.query(models.Inventory)
            .filter(models.Inventory.workshop_id == w.id)
            .all()
        )
        produced = sum(i.current_stock for i in invs if i.is_finished)
        load_percent = (produced / plan_output * 100.0) if plan_output and plan_output > 0 else 0.0
        result.append({
            "workshop_id": w.id,
            "workshop_name": w.name,
            "plan_output": plan_output,
            "produced_today": produced,
            "load_percent": round(load_percent, 2),
        })
    return {"workshops": result}