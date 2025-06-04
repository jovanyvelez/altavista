from enum import Enum

class RolUsuarioEnum(str, Enum):
    ADMINISTRADOR = "administrador"
    PROPIETARIO_CONSULTA = "propietario_consulta"

class TipoMovimientoEnum(str, Enum):
    DEBITO = "DEBITO"
    CREDITO = "CREDITO"

class TipoItemPresupuestoEnum(str, Enum):
    INGRESO = "INGRESO"
    GASTO = "GASTO"
