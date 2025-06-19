from sqlmodel import SQLModel, Field
from decimal import Decimal
from typing import Optional

class TasaInteresMora(SQLModel, table=True):
    __tablename__ = "tasa_interes_mora"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    año: int
    mes: int = Field(ge=1, le=12)
    tasa_interes_mensual: Decimal = Field(decimal_places=4, max_digits=5)
