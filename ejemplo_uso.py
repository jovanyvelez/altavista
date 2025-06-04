# Ejemplo de uso de los modelos SQLModel

from app.models import (
    db_manager, 
    Propietario, 
    Apartamento, 
    Concepto, 
    PresupuestoAnual,
    RolUsuarioEnum
)

def ejemplo_uso():
    """Ejemplo de cómo usar los modelos creados"""
    
    # 1. Crear las tablas en la base de datos
    db_manager.create_tables()
    
    # 2. Crear algunos datos de ejemplo
    with db_manager.get_session() as session:
        # Crear un propietario
        propietario = Propietario(
            nombre_completo="Juan Pérez",
            documento_identidad="12345678",
            email="juan.perez@email.com",
            telefono="555-1234"
        )
        session.add(propietario)
        session.commit()
        session.refresh(propietario)
        
        # Crear un apartamento
        apartamento = Apartamento(
            identificador="Apto 101",
            coeficiente_copropiedad=0.012500,
            propietario_id=propietario.id
        )
        session.add(apartamento)
        session.commit()
        
        # Crear un concepto
        concepto = Concepto(
            nombre="Cuota de Administración",
            es_ingreso_tipico=True,
            es_recurrente_presupuesto=True,
            descripcion="Cuota mensual de administración"
        )
        session.add(concepto)
        session.commit()
        
        # Crear un presupuesto anual
        presupuesto = PresupuestoAnual(
            año=2025,
            descripcion="Presupuesto anual 2025"
        )
        session.add(presupuesto)
        session.commit()
        
        print("¡Datos de ejemplo creados exitosamente!")

if __name__ == "__main__":
    ejemplo_uso()
