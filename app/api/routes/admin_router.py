from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import UnitPrice, PriceType
from app.schemas import (
    UnitPriceResponse,
    ElectricityPriceCreate, StayPriceCreate, 
    GasPriceCreate, FirewoodPriceCreate
)

router = APIRouter(prefix="/admin", tags=["admin"])


# Electricity price endpoints
@router.post("/pricing/electricity", response_model=UnitPriceResponse)
def create_electricity_price(
    price_data: ElectricityPriceCreate,
    db: Session = Depends(get_db)
):
    """Create electricity price in EUR per kWh."""
    unit_price = UnitPrice(
        price_type=PriceType.ELECTRICITY_PER_KWH,
        **price_data.dict()
    )
    db.add(unit_price)
    db.commit()
    db.refresh(unit_price)
    return unit_price


@router.get("/pricing/electricity", response_model=List[UnitPriceResponse])
def list_electricity_prices(db: Session = Depends(get_db)):
    """List all electricity prices."""
    return db.query(UnitPrice).filter(
        UnitPrice.price_type == PriceType.ELECTRICITY_PER_KWH
    ).order_by(UnitPrice.effective_from.desc()).all()


# Stay price endpoints
@router.post("/pricing/stay", response_model=UnitPriceResponse)
def create_stay_price(
    price_data: StayPriceCreate,
    db: Session = Depends(get_db)
):
    """Create accommodation price in EUR per night."""
    unit_price = UnitPrice(
        price_type=PriceType.STAY_PER_NIGHT,
        **price_data.dict()
    )
    db.add(unit_price)
    db.commit()
    db.refresh(unit_price)
    return unit_price


@router.get("/pricing/stay", response_model=List[UnitPriceResponse])
def list_stay_prices(db: Session = Depends(get_db)):
    """List all accommodation prices."""
    return db.query(UnitPrice).filter(
        UnitPrice.price_type == PriceType.STAY_PER_NIGHT
    ).order_by(UnitPrice.effective_from.desc()).all()


# Gas price endpoints
@router.post("/pricing/gas", response_model=UnitPriceResponse)
def create_gas_price(
    price_data: GasPriceCreate,
    db: Session = Depends(get_db)
):
    """Create gas price in EUR per cubic meter."""
    unit_price = UnitPrice(
        price_type=PriceType.GAS_PER_CUBIC_METER,
        **price_data.dict()
    )
    db.add(unit_price)
    db.commit()
    db.refresh(unit_price)
    return unit_price


@router.get("/pricing/gas", response_model=List[UnitPriceResponse])
def list_gas_prices(db: Session = Depends(get_db)):
    """List all gas prices."""
    return db.query(UnitPrice).filter(
        UnitPrice.price_type == PriceType.GAS_PER_CUBIC_METER
    ).order_by(UnitPrice.effective_from.desc()).all()


# Firewood price endpoints
@router.post("/pricing/firewood", response_model=UnitPriceResponse)
def create_firewood_price(
    price_data: FirewoodPriceCreate,
    db: Session = Depends(get_db)
):
    """Create firewood price in EUR per box."""
    unit_price = UnitPrice(
        price_type=PriceType.FIREWOOD_PER_BOX,
        **price_data.dict()
    )
    db.add(unit_price)
    db.commit()
    db.refresh(unit_price)
    return unit_price


@router.get("/pricing/firewood", response_model=List[UnitPriceResponse])
def list_firewood_prices(db: Session = Depends(get_db)):
    """List all firewood prices."""
    return db.query(UnitPrice).filter(
        UnitPrice.price_type == PriceType.FIREWOOD_PER_BOX
    ).order_by(UnitPrice.effective_from.desc()).all()

