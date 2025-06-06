from enum import Enum

class RolUsuarioEnum(str, Enum):
    administrador = "administrador"
    propietario_consulta = "propietario_consulta"

class TipoMovimientoEnum(str, Enum):
    CARGO = "cargo"
    ABONO = "abono"

class TipoItemPresupuestoEnum(str, Enum):
    INGRESO = "INGRESO"
    GASTO = "GASTO"
