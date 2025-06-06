from sqlmodel import Session, select
from app.models import (
    db_manager, Usuario, Propietario, Apartamento, Concepto,
    PresupuestoAnual, RolUsuarioEnum, TipoMovimientoEnum,
    RegistroFinancieroApartamento, ItemPresupuesto, TipoItemPresupuestoEnum
)
from datetime import datetime

async def crear_datos_iniciales():
    """Crear algunos datos de ejemplo para testing"""
    with db_manager.get_session() as session:
        # Verificar si ya existen datos
        admin_existente = session.exec(
            select(Usuario).where(Usuario.username == "admin")
        ).first()
        
        if not admin_existente:
            # Crear conceptos básicos
            conceptos = [
                Concepto(nombre="Cuota Ordinaria Administración", es_ingreso_tipico=True),
                Concepto(nombre="Mantenimiento Ascensor", es_ingreso_tipico=False),
                Concepto(nombre="Servicios Públicos", es_ingreso_tipico=False),
                Concepto(nombre="Vigilancia", es_ingreso_tipico=False),
                Concepto(nombre="Aseo", es_ingreso_tipico=False),
            ]
            for concepto in conceptos:
                session.add(concepto)
            session.commit()

            # Crear usuario administrador
            admin_usuario = Usuario(
                username="admin",
                password="admin123",  # En producción debería estar hasheada
                nombre_completo="Administrador del Sistema",
                email="admin@edificio.com",
                rol=RolUsuarioEnum.ADMIN
            )
            session.add(admin_usuario)
            session.commit()

            # Crear algunos apartamentos
            apartamentos = [
                Apartamento(numero="101", piso=1, propietario_id=None),
                Apartamento(numero="102", piso=1, propietario_id=None),
                Apartamento(numero="201", piso=2, propietario_id=None),
                Apartamento(numero="202", piso=2, propietario_id=None),
                Apartamento(numero="301", piso=3, propietario_id=None),
                Apartamento(numero="302", piso=3, propietario_id=None),
            ]
            for apartamento in apartamentos:
                session.add(apartamento)
            session.commit()

            # Crear propietarios de ejemplo
            propietarios = [
                {
                    "usuario": Usuario(
                        username="prop101",
                        password="prop123",
                        nombre_completo="María García",
                        email="maria@email.com",
                        rol=RolUsuarioEnum.PROPIETARIO
                    ),
                    "propietario": Propietario(
                        nombre="María García",
                        telefono="123456789",
                        email="maria@email.com"
                    ),
                    "apartamento": "101"
                },
                {
                    "usuario": Usuario(
                        username="prop201",
                        password="prop123",
                        nombre_completo="Juan Pérez",
                        email="juan@email.com",
                        rol=RolUsuarioEnum.PROPIETARIO
                    ),
                    "propietario": Propietario(
                        nombre="Juan Pérez",
                        telefono="987654321",
                        email="juan@email.com"
                    ),
                    "apartamento": "201"
                }
            ]

            for prop_data in propietarios:
                # Crear usuario
                session.add(prop_data["usuario"])
                session.commit()
                session.refresh(prop_data["usuario"])

                # Crear propietario
                prop_data["propietario"].usuario_id = prop_data["usuario"].id
                session.add(prop_data["propietario"])
                session.commit()
                session.refresh(prop_data["propietario"])

                # Asignar apartamento
                apartamento = session.exec(
                    select(Apartamento).where(Apartamento.numero == prop_data["apartamento"])
                ).first()
                if apartamento:
                    apartamento.propietario_id = prop_data["propietario"].id
                    session.add(apartamento)

            session.commit()

            # Crear presupuesto anual
            presupuesto = PresupuestoAnual(
                año=datetime.now().year,
                descripcion="Presupuesto anual de prueba",
                total_presupuestado=0
            )
            session.add(presupuesto)
            session.commit()

            # Crear items del presupuesto
            items_presupuesto = [
                ItemPresupuesto(
                    presupuesto_id=presupuesto.id,
                    concepto_id=conceptos[0].id,
                    tipo=TipoItemPresupuestoEnum.INGRESO,
                    monto_presupuestado=1000000,
                    descripcion="Cuotas de administración anuales"
                ),
                ItemPresupuesto(
                    presupuesto_id=presupuesto.id,
                    concepto_id=conceptos[1].id,
                    tipo=TipoItemPresupuestoEnum.GASTO,
                    monto_presupuestado=600000,
                    descripcion="Mantenimiento preventivo ascensor"
                ),
                ItemPresupuesto(
                    presupuesto_id=presupuesto.id,
                    concepto_id=conceptos[2].id,
                    tipo=TipoItemPresupuestoEnum.GASTO,
                    monto_presupuestado=200000,
                    descripcion="Servicios públicos zonas comunes"
                )
            ]

            for item in items_presupuesto:
                session.add(item)

            # Actualizar total del presupuesto
            presupuesto.total_presupuestado = sum(
                item.monto_presupuestado for item in items_presupuesto 
                if item.tipo == TipoItemPresupuestoEnum.INGRESO
            )
            
            session.commit()

            print("Datos iniciales creados exitosamente")
        else:
            print("Los datos iniciales ya existen")
