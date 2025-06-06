from fastapi import APIRouter, Request, Form, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select, func
from typing import Optional, List
from datetime import datetime, date
from app.models import (
    db_manager, Apartamento, Concepto, TipoMovimientoEnum,
    RegistroFinancieroApartamento, CuotaConfiguracion
)
from app.dependencies import templates, require_admin, get_db_session

router = APIRouter(prefix="/admin/pagos", dependencies=[Depends(require_admin)])

@router.get("", response_class=HTMLResponse)
async def admin_pagos(
    request: Request,
    mes: Optional[int] = None,
    año: Optional[int] = None
):
    """Dashboard principal del sistema de pagos"""
    # Usar mes y año actuales si no se especifican
    if not mes:
        mes = datetime.now().month
    if not año:
        año = datetime.now().year
    
    with get_db_session() as session:
        # Obtener el concepto de cuota ordinaria
        concepto_cuota = session.exec(
            select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%administr%"))
        ).first()
        
        if not concepto_cuota:
            # Si no existe, crear el concepto
            concepto_cuota = Concepto(
                nombre="Cuota Ordinaria Administración",
                es_ingreso_tipico=True
            )
            session.add(concepto_cuota)
            session.commit()
            session.refresh(concepto_cuota)
        
        # Obtener todos los apartamentos
        apartamentos = session.exec(select(Apartamento)).all()
        total_apartamentos = len(apartamentos)
        
        # Obtener pagos realizados este mes
        pagos_mes = []
        total_recaudado = 0
        apartamentos_pagados = 0
        apartamentos_pendientes = []
        
        if concepto_cuota:
            # Pagos realizados este mes
            pagos_mes = session.exec(
                select(RegistroFinancieroApartamento)
                .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id)
                .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.ABONO)
                .where(RegistroFinancieroApartamento.mes_aplicable == mes)
                .where(RegistroFinancieroApartamento.año_aplicable == año)
            ).all()
            
            total_recaudado = sum(pago.monto for pago in pagos_mes)
            apartamentos_pagados = len(set(pago.apartamento_id for pago in pagos_mes))
            
            # Apartamentos que han pagado este mes
            apartamentos_ids_pagados = {pago.apartamento_id for pago in pagos_mes}
            
            # Apartamentos pendientes de pago
            apartamentos_pendientes = [
                apt for apt in apartamentos 
                if apt.id not in apartamentos_ids_pagados
            ]
        
        # Generar datos para el gráfico
        meses_labels = []
        recaudacion_data = []
        
        for i in range(6):  # Últimos 6 meses
            mes_calc = mes - i
            año_calc = año
            if mes_calc <= 0:
                mes_calc += 12
                año_calc -= 1
            
            meses_labels.insert(0, f"{mes_calc:02d}/{año_calc}")
            
            recaudado_mes = session.exec(
                select(func.sum(RegistroFinancieroApartamento.monto))
                .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id)
                .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.ABONO)
                .where(RegistroFinancieroApartamento.mes_aplicable == mes_calc)
                .where(RegistroFinancieroApartamento.año_aplicable == año_calc)
            ).first() or 0
            
            recaudacion_data.insert(0, float(recaudado_mes))
        
        return templates.TemplateResponse(
            "admin/pagos.html",
            {
                "request": request,
                "mes_actual": mes,
                "año_actual": año,
                "total_apartamentos": total_apartamentos,
                "apartamentos_pagados": apartamentos_pagados,
                "apartamentos_pendientes": len(apartamentos_pendientes),
                "total_recaudado": total_recaudado,
                "porcentaje_recaudacion": round((apartamentos_pagados / total_apartamentos * 100) if total_apartamentos > 0 else 0, 1),
                "apartamentos_pendientes_lista": apartamentos_pendientes,
                "pagos_mes": pagos_mes,
                "meses_labels": meses_labels,
                "recaudacion_data": recaudacion_data
            }
        )

@router.get("/configuracion", response_class=HTMLResponse)
async def admin_pagos_configuracion(
    request: Request,
    mes: Optional[int] = None,
    año: Optional[int] = None
):
    """Configuración de cuotas mensuales"""
    # Usar mes y año actuales si no se especifican
    if not mes:
        mes = datetime.now().month
    if not año:
        año = datetime.now().year
    
    with get_db_session() as session:
        # Obtener todos los apartamentos con sus configuraciones
        apartamentos = session.exec(select(Apartamento)).all()
        
        # Obtener configuraciones existentes para el mes/año
        configuraciones = session.exec(
            select(CuotaConfiguracion)
            .where(CuotaConfiguracion.mes == mes)
            .where(CuotaConfiguracion.año == año)
        ).all()
        
        # Crear diccionario para acceso rápido
        config_dict = {config.apartamento_id: config for config in configuraciones}
        
        return templates.TemplateResponse(
            "admin/pagos_configuracion.html",
            {
                "request": request,
                "apartamentos": apartamentos,
                "configuraciones": config_dict,
                "mes_actual": mes,
                "año_actual": año
            }
        )

@router.post("/configuracion/guardar")
async def guardar_configuracion_cuotas(
    request: Request,
    mes: int = Form(...),
    año: int = Form(...),
    montos: List[float] = Form(...)
):
    """Guardar configuración de cuotas para el mes"""
    with get_db_session() as session:
        # Obtener todos los apartamentos
        apartamentos = session.exec(select(Apartamento)).all()
        
        if len(montos) != len(apartamentos):
            return RedirectResponse(
                url="/admin/pagos/configuracion?error=data_mismatch",
                status_code=status.HTTP_302_FOUND
            )
        
        # Eliminar configuraciones existentes para el mes/año
        configuraciones_existentes = session.exec(
            select(CuotaConfiguracion)
            .where(CuotaConfiguracion.mes == mes)
            .where(CuotaConfiguracion.año == año)
        ).all()
        
        for config in configuraciones_existentes:
            session.delete(config)
        
        # Crear nuevas configuraciones
        for i, apartamento in enumerate(apartamentos):
            if i < len(montos) and montos[i] > 0:
                nueva_config = CuotaConfiguracion(
                    apartamento_id=apartamento.id,
                    mes=mes,
                    año=año,
                    monto_cuota=montos[i],
                    fecha_creacion=datetime.now()
                )
                session.add(nueva_config)
        
        session.commit()
    
    return RedirectResponse(
        url="/admin/pagos/configuracion?success=1",
        status_code=status.HTTP_302_FOUND
    )

@router.get("/generar-cargos", response_class=HTMLResponse)
async def admin_pagos_generar_cargos(request: Request):
    """Página para generar cargos automáticos"""
    mes_actual = datetime.now().month
    año_actual = datetime.now().year
    
    with get_db_session() as session:
        # Verificar si existen configuraciones para el mes actual
        configuraciones = session.exec(
            select(CuotaConfiguracion)
            .where(CuotaConfiguracion.mes == mes_actual)
            .where(CuotaConfiguracion.año == año_actual)
        ).all()
        
        return templates.TemplateResponse(
            "admin/pagos_generar_cargos.html",
            {
                "request": request,
                "mes_actual": mes_actual,
                "año_actual": año_actual,
                "configuraciones_disponibles": len(configuraciones)
            }
        )

@router.post("/generar-cargos")
async def generar_cargos_automaticos(
    request: Request,
    mes: int = Form(...),
    año: int = Form(...)
):
    """Generar cargos automáticos basados en la configuración"""
    with get_db_session() as session:
        # Obtener el concepto de cuota ordinaria
        concepto_cuota = session.exec(
            select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%administr%"))
        ).first()
        
        if not concepto_cuota:
            return RedirectResponse(
                url="/admin/pagos/generar-cargos?error=no_concept",
                status_code=status.HTTP_302_FOUND
            )
        
        # Obtener configuraciones para el mes/año
        configuraciones = session.exec(
            select(CuotaConfiguracion)
            .where(CuotaConfiguracion.mes == mes)
            .where(CuotaConfiguracion.año == año)
        ).all()
        
        if not configuraciones:
            return RedirectResponse(
                url="/admin/pagos/generar-cargos?error=no_config",
                status_code=status.HTTP_302_FOUND
            )
        
        # Verificar si ya existen cargos para este mes/año
        cargos_existentes = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id)
            .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.CARGO)
            .where(RegistroFinancieroApartamento.mes_aplicable == mes)
            .where(RegistroFinancieroApartamento.año_aplicable == año)
        ).first()
        
        if cargos_existentes:
            return RedirectResponse(
                url="/admin/pagos/generar-cargos?error=already_exists",
                status_code=status.HTTP_302_FOUND
            )
        
        # Generar cargos
        cargos_creados = 0
        fecha_cargo = date(año, mes, 1)  # Primer día del mes
        
        for config in configuraciones:
            nuevo_cargo = RegistroFinancieroApartamento(
                apartamento_id=config.apartamento_id,
                concepto_id=concepto_cuota.id,
                tipo_movimiento=TipoMovimientoEnum.CARGO,
                monto=config.monto_cuota,
                fecha_efectiva=fecha_cargo,
                mes_aplicable=mes,
                año_aplicable=año,
                referencia_pago=f"CARGO-AUTO-{mes:02d}/{año}",
                descripcion_adicional=f"Cuota ordinaria de administración - {mes:02d}/{año}",
                fecha_creacion=datetime.now()
            )
            session.add(nuevo_cargo)
            cargos_creados += 1
        
        session.commit()
    
    return RedirectResponse(
        url=f"/admin/pagos/generar-cargos?success={cargos_creados}",
        status_code=status.HTTP_302_FOUND
    )

@router.get("/procesar", response_class=HTMLResponse)
async def admin_pagos_procesar(request: Request):
    """Página para procesar pagos individuales"""
    with get_db_session() as session:
        # Obtener apartamentos y concepto de cuota
        apartamentos = session.exec(select(Apartamento)).all()
        concepto_cuota = session.exec(
            select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%administr%"))
        ).first()
        
        return templates.TemplateResponse(
            "admin/pagos_procesar.html",
            {
                "request": request,
                "apartamentos": apartamentos,
                "concepto_cuota": concepto_cuota
            }
        )

@router.post("/procesar")
async def procesar_pago_individual(
    request: Request,
    apartamento_id: int = Form(...),
    monto: float = Form(...),
    fecha_pago: date = Form(...),
    mes_aplicable: int = Form(...),
    año_aplicable: int = Form(...),
    referencia_pago: Optional[str] = Form(None),
    observaciones: Optional[str] = Form(None)
):
    """Procesar pago individual"""
    with get_db_session() as session:
        # Obtener el concepto de cuota ordinaria
        concepto_cuota = session.exec(
            select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%administr%"))
        ).first()
        
        if not concepto_cuota:
            return RedirectResponse(
                url="/admin/pagos/procesar?error=no_concept",
                status_code=status.HTTP_302_FOUND
            )
        
        # Crear registro de pago
        nuevo_pago = RegistroFinancieroApartamento(
            apartamento_id=apartamento_id,
            concepto_id=concepto_cuota.id,
            tipo_movimiento=TipoMovimientoEnum.ABONO,
            monto=monto,
            fecha_efectiva=fecha_pago,
            mes_aplicable=mes_aplicable,
            año_aplicable=año_aplicable,
            referencia_pago=referencia_pago or f"PAGO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            descripcion_adicional=observaciones or "Pago procesado por administrador",
            fecha_creacion=datetime.now()
        )
        
        session.add(nuevo_pago)
        session.commit()
    
    return RedirectResponse(
        url="/admin/pagos/procesar?success=1",
        status_code=status.HTTP_302_FOUND
    )

@router.get("/reportes", response_class=HTMLResponse)
async def admin_pagos_reportes(
    request: Request,
    mes: Optional[int] = None,
    año: Optional[int] = None
):
    """Reportes del sistema de pagos"""
    # Usar mes y año actuales si no se especifican
    if not mes:
        mes = datetime.now().month
    if not año:
        año = datetime.now().year
    
    with get_db_session() as session:
        # Obtener el concepto de cuota ordinaria
        concepto_cuota = session.exec(
            select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%administr%"))
        ).first()
        
        # Obtener todos los apartamentos con sus pagos
        apartamentos = session.exec(select(Apartamento)).all()
        
        reporte_apartamentos = []
        total_cargado = 0
        total_pagado = 0
        
        for apartamento in apartamentos:
            # Cargos del mes
            cargos = session.exec(
                select(func.sum(RegistroFinancieroApartamento.monto))
                .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
                .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id)
                .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.CARGO)
                .where(RegistroFinancieroApartamento.mes_aplicable == mes)
                .where(RegistroFinancieroApartamento.año_aplicable == año)
            ).first() or 0
            
            # Pagos del mes
            pagos = session.exec(
                select(func.sum(RegistroFinancieroApartamento.monto))
                .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
                .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id)
                .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.ABONO)
                .where(RegistroFinancieroApartamento.mes_aplicable == mes)
                .where(RegistroFinancieroApartamento.año_aplicable == año)
            ).first() or 0
            
            saldo = float(pagos) - float(cargos)
            estado = "Pagado" if saldo >= 0 else "Pendiente"
            
            reporte_apartamentos.append({
                "apartamento": apartamento,
                "cargos": float(cargos),
                "pagos": float(pagos),
                "saldo": saldo,
                "estado": estado
            })
            
            total_cargado += float(cargos)
            total_pagado += float(pagos)
        
        return templates.TemplateResponse(
            "admin/pagos_reportes.html",
            {
                "request": request,
                "mes_actual": mes,
                "año_actual": año,
                "reporte_apartamentos": reporte_apartamentos,
                "total_cargado": total_cargado,
                "total_pagado": total_pagado,
                "total_pendiente": total_cargado - total_pagado,
                "porcentaje_recaudacion": round((total_pagado / total_cargado * 100) if total_cargado > 0 else 0, 1)
            }
        )
