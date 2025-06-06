from enum import Enum

class RolUsuarioEnum(str, Enum):
    ADMIN = "ADMIN"
    PROPIETARIO = "PROPIETARIO"

class TipoMovimientoEnum(str, Enum):
    DEBITO = "DEBITO"  # Para cargos/deudas del apartamento
    CREDITO = "CREDITO"  # Para pagos/abonos del apartamento

class TipoItemPresupuestoEnum(str, Enum):
    INGRESO = "INGRESO"
    GASTO = "GASTO"
