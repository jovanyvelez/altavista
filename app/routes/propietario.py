from fastapi import APIRouter, Request, Form, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select, func
from typing import Optional
from datetime import datetime, date
from app.models import (
    db_manager, Usuario, Propietario, Apartamento, Concepto,
    TipoMovimientoEnum, RegistroFinancieroApartamento
)
from app.dependencies import templates, require_propietario, get_db_session

router = APIRouter(prefix="/propietario", dependencies=[Depends(require_propietario)])

@router.get("/dashboard", response_class=HTMLResponse)
async def propietario_dashboard(request: Request):
    """Dashboard del propietario"""
    user, propietario = require_propietario(request)
    
    with get_db_session() as session:
        # Obtener apartamento del propietario
        apartamento = session.exec(
            select(Apartamento).where(Apartamento.propietario_id == propietario.id)
        ).first()
        
        if not apartamento:
            return templates.TemplateResponse("propietario/dashboard.html", {
                "request": request,
                "propietario": propietario,
                "apartamento": None,
                "error": "No tiene apartamento asignado"
            })
        
        # Obtener estadísticas financieras
        total_cargos = session.exec(
            select(func.sum(RegistroFinancieroApartamento.monto))
            .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
            .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.CARGO)
        ).first() or 0
        
        total_abonos = session.exec(
            select(func.sum(RegistroFinancieroApartamento.monto))
            .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
            .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.ABONO)
        ).first() or 0
        
        saldo_actual = float(total_abonos) - float(total_cargos)
        
        # Obtener registros recientes
        registros_recientes = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
            .order_by(RegistroFinancieroApartamento.fecha_efectiva.desc())
            .limit(5)
        ).all()
        
        return templates.TemplateResponse("propietario/dashboard.html", {
            "request": request,
            "propietario": propietario,
            "apartamento": apartamento,
            "total_cargos": total_cargos,
            "total_abonos": total_abonos,
            "saldo_actual": saldo_actual,
            "registros_recientes": registros_recientes
        })

@router.get("/estado-cuenta", response_class=HTMLResponse)
async def propietario_estado_cuenta(request: Request):
    """Estado de cuenta del propietario"""
    user, propietario = require_propietario(request)
    
    with get_db_session() as session:
        # Obtener apartamento del propietario
        apartamento = session.exec(
            select(Apartamento).where(Apartamento.propietario_id == propietario.id)
        ).first()
        
        if not apartamento:
            raise HTTPException(status_code=404, detail="Apartamento no encontrado")
        
        # Obtener todos los registros financieros
        registros = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
            .order_by(RegistroFinancieroApartamento.fecha_efectiva.desc())
        ).all()
        
        # Calcular totales
        total_cargos = sum(
            r.monto for r in registros 
            if r.tipo_movimiento == TipoMovimientoEnum.CARGO
        )
        total_abonos = sum(
            r.monto for r in registros 
            if r.tipo_movimiento == TipoMovimientoEnum.ABONO
        )
        saldo_actual = total_abonos - total_cargos
        
        return templates.TemplateResponse("propietario/estado_cuenta.html", {
            "request": request,
            "propietario": propietario,
            "apartamento": apartamento,
            "registros": registros,
            "total_cargos": total_cargos,
            "total_abonos": total_abonos,
            "saldo_actual": saldo_actual
        })

@router.get("/mis-pagos", response_class=HTMLResponse)
async def propietario_mis_pagos(
    request: Request,
    reporte_enviado: Optional[int] = None
):
    """Vista de pagos del propietario"""
    user, propietario = require_propietario(request)
    
    with get_db_session() as session:
        # Obtener apartamento del propietario
        apartamento = session.exec(
            select(Apartamento).where(Apartamento.propietario_id == propietario.id)
        ).first()
        
        if not apartamento:
            raise HTTPException(status_code=404, detail="Apartamento no encontrado")
        
        # Obtener el concepto de cuota ordinaria
        concepto_cuota = session.exec(
            select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%administr%"))
        ).first()
        
        # Obtener historial de pagos de cuotas ordinarias
        pagos_cuotas = []
        if concepto_cuota:
            pagos_cuotas = session.exec(
                select(RegistroFinancieroApartamento)
                .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
                .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id)
                .order_by(RegistroFinancieroApartamento.fecha_efectiva.desc())
            ).all()
        
        # Agrupar por mes/año para mostrar estado de pagos
        pagos_por_mes = {}
        for pago in pagos_cuotas:
            key = f"{pago.año_aplicable}-{pago.mes_aplicable:02d}"
            if key not in pagos_por_mes:
                pagos_por_mes[key] = {"cargos": 0, "pagos": 0, "registros": []}
            
            if pago.tipo_movimiento == TipoMovimientoEnum.CARGO:
                pagos_por_mes[key]["cargos"] += pago.monto
            else:
                pagos_por_mes[key]["pagos"] += pago.monto
            
            pagos_por_mes[key]["registros"].append(pago)
        
        # Calcular estado de cada mes
        estados_mensuales = []
        for mes_año, data in sorted(pagos_por_mes.items(), reverse=True):
            año, mes = mes_año.split("-")
            saldo = data["pagos"] - data["cargos"]
            estado = "Pagado" if saldo >= 0 else "Pendiente"
            
            estados_mensuales.append({
                "mes": int(mes),
                "año": int(año),
                "mes_nombre": datetime(int(año), int(mes), 1).strftime("%B"),
                "cargos": data["cargos"],
                "pagos": data["pagos"],
                "saldo": saldo,
                "estado": estado,
                "registros": data["registros"]
            })
        
        return templates.TemplateResponse("propietario/mis_pagos.html", {
            "request": request,
            "propietario": propietario,
            "apartamento": apartamento,
            "estados_mensuales": estados_mensuales,
            "reporte_enviado": reporte_enviado,
            "concepto_cuota": concepto_cuota
        })

@router.post("/reportar-pago")
async def reportar_pago(
    request: Request,
    monto_reportado: float = Form(...),
    fecha_pago_reportado: str = Form(...),
    metodo_pago: str = Form(...),
    referencia_reportada: Optional[str] = Form(None),
    observaciones: Optional[str] = Form(None)
):
    """Reportar pago realizado por el propietario"""
    user, propietario = require_propietario(request)
    
    with get_db_session() as session:
        # Obtener apartamento del propietario
        apartamento = session.exec(
            select(Apartamento).where(Apartamento.propietario_id == propietario.id)
        ).first()
        
        if not apartamento:
            raise HTTPException(status_code=404, detail="Apartamento no encontrado")
        
        # Obtener el concepto de cuota ordinaria
        concepto_cuota = session.exec(
            select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%administr%"))
        ).first()
        
        if not concepto_cuota:
            raise HTTPException(status_code=404, detail="Concepto de cuota no encontrado")
        
        # Crear registro de reporte de pago (pendiente de validación)
        reporte_pago = RegistroFinancieroApartamento(
            apartamento_id=apartamento.id,
            concepto_id=concepto_cuota.id,
            tipo_movimiento=TipoMovimientoEnum.ABONO,
            monto=monto_reportado,
            fecha_efectiva=datetime.strptime(fecha_pago_reportado, "%Y-%m-%d").date(),
            mes_aplicable=datetime.now().month,
            año_aplicable=datetime.now().year,
            referencia_pago=f"REPORTE-{metodo_pago}: {referencia_reportada or 'Sin referencia'}",
            descripcion_adicional=f"PENDIENTE VALIDACIÓN - {observaciones or 'Pago reportado por propietario'}",
            fecha_creacion=datetime.now()
        )
        
        session.add(reporte_pago)
        session.commit()
    
    return RedirectResponse(
        url="/propietario/mis-pagos?reporte_enviado=1",
        status_code=status.HTTP_302_FOUND
    )
