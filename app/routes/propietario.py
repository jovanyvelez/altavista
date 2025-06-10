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
        # Obtener todos los apartamentos del propietario
        apartamentos = session.exec(
            select(Apartamento).where(Apartamento.propietario_id == propietario.id)
        ).all()
        
        if not apartamentos:
            return templates.TemplateResponse("propietario/dashboard.html", {
                "request": request,
                "user": user,
                "propietario": propietario,
                "apartamentos": None,
                "error": "No tiene apartamentos asignados"
            })
        
        # Calcular estadísticas financieras para todos los apartamentos
        total_cargos = 0
        total_abonos = 0
        registros_recientes = []
        
        for apartamento in apartamentos:
            # Obtener cargos del apartamento
            cargos_apt = session.exec(
                select(func.sum(RegistroFinancieroApartamento.monto))
                .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
                .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.DEBITO)
            ).first() or 0
            
            # Obtener abonos del apartamento
            abonos_apt = session.exec(
                select(func.sum(RegistroFinancieroApartamento.monto))
                .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
                .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.CREDITO)
            ).first() or 0
            
            total_cargos += float(cargos_apt)
            total_abonos += float(abonos_apt)
            
            # Obtener registros recientes del apartamento
            registros_apt = session.exec(
                select(RegistroFinancieroApartamento)
                .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
                .order_by(RegistroFinancieroApartamento.fecha_efectiva.desc())
                .limit(3)  # Menos registros por apartamento para no sobrecargar
            ).all()
            registros_recientes.extend(registros_apt)
        
        # Ordenar todos los registros recientes por fecha
        registros_recientes.sort(key=lambda x: x.fecha_efectiva, reverse=True)
        registros_recientes = registros_recientes[:5]  # Mantener solo los 5 más recientes
        
        saldo_actual = total_cargos - total_abonos  # Saldo pendiente (deuda)
        
        return templates.TemplateResponse("propietario/dashboard.html", {
            "request": request,
            "user": user,
            "propietario": propietario,
            "apartamentos": apartamentos,  # Cambio de 'apartamento' a 'apartamentos'
            "total_cargos": total_cargos,
            "total_abonos": total_abonos,
            "saldo_actual": saldo_actual,
            "registros_recientes": registros_recientes
        })

@router.get("/estado-cuenta", response_class=HTMLResponse)
async def propietario_estado_cuenta(request: Request, apartamento: Optional[int] = None):
    """Estado de cuenta del propietario"""
    user, propietario = require_propietario(request)
    
    with get_db_session() as session:
        # Obtener apartamentos del propietario
        apartamentos_propietario = session.exec(
            select(Apartamento).where(Apartamento.propietario_id == propietario.id)
        ).all()
        
        if not apartamentos_propietario:
            raise HTTPException(status_code=404, detail="No tienes apartamentos asignados")
        
        # Si se especifica un apartamento, verificar que pertenezca al propietario
        apartamento_seleccionado = None
        if apartamento:
            apartamento_seleccionado = session.exec(
                select(Apartamento)
                .where(Apartamento.id == apartamento)
                .where(Apartamento.propietario_id == propietario.id)
            ).first()
            
            if not apartamento_seleccionado:
                raise HTTPException(status_code=403, detail="No tienes acceso a este apartamento")
        else:
            # Si no se especifica, usar el primer apartamento
            apartamento_seleccionado = apartamentos_propietario[0]
        
        # Obtener todos los registros financieros del apartamento seleccionado
        registros_raw = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.apartamento_id == apartamento_seleccionado.id)
            .order_by(RegistroFinancieroApartamento.fecha_efectiva.desc())
        ).all()
        
        # Cargar las relaciones manualmente
        registros = []
        for reg in registros_raw:
            # Obtener apartamento
            apartamento = session.exec(
                select(Apartamento).where(Apartamento.id == reg.apartamento_id)
            ).first()
            
            # Obtener concepto
            concepto = session.exec(
                select(Concepto).where(Concepto.id == reg.concepto_id)
            ).first()
            
            # Agregar las relaciones al objeto registro
            reg.apartamento = apartamento
            reg.concepto = concepto
            registros.append(reg)
        
        # Preparar saldos por apartamento (formato que espera el template)
        saldos_por_apartamento = {}
        saldo_total = 0
        
        for apartamento_prop in apartamentos_propietario:
            # Calcular saldo para este apartamento
            registros_apt = [r for r in registros if r.apartamento_id == apartamento_prop.id]
            
            total_cargos = sum(
                r.monto for r in registros_apt 
                if r.tipo_movimiento == TipoMovimientoEnum.DEBITO
            )
            total_abonos = sum(
                r.monto for r in registros_apt 
                if r.tipo_movimiento == TipoMovimientoEnum.CREDITO
            )
            saldo_apartamento = total_cargos - total_abonos
            
            saldos_por_apartamento[apartamento_prop.id] = {
                'apartamento': apartamento_prop,
                'saldo': saldo_apartamento
            }
            saldo_total += saldo_apartamento
        
        # Calcular totales del apartamento seleccionado
        total_cargos = sum(
            r.monto for r in registros 
            if r.tipo_movimiento == TipoMovimientoEnum.DEBITO
        )
        total_abonos = sum(
            r.monto for r in registros 
            if r.tipo_movimiento == TipoMovimientoEnum.CREDITO
        )
        saldo_actual = total_cargos - total_abonos
        
        return templates.TemplateResponse("propietario/estado_cuenta.html", {
            "request": request,
            "propietario": propietario,
            "apartamento": apartamento_seleccionado,
            "apartamentos": apartamentos_propietario,
            "registros": registros,
            "saldos_por_apartamento": saldos_por_apartamento,
            "saldo_total": saldo_total,
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
            
            if pago.tipo_movimiento == TipoMovimientoEnum.DEBITO:
                pagos_por_mes[key]["cargos"] += pago.monto
            else:
                pagos_por_mes[key]["pagos"] += pago.monto
            
            pagos_por_mes[key]["registros"].append(pago)
        
        # Calcular estado de cada mes
        estados_mensuales = []
        total_cargos_general = 0
        total_abonos_general = 0
        
        for mes_año, data in sorted(pagos_por_mes.items(), reverse=True):
            año, mes = mes_año.split("-")
            saldo = data["pagos"] - data["cargos"]
            estado = "Pagado" if saldo >= 0 else "Pendiente"
            
            total_cargos_general += data["cargos"]
            total_abonos_general += data["pagos"]
            
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
        
        # Calcular saldo total
        saldo_total = total_cargos_general - total_abonos_general
        
        # Crear diccionario de estados de pago por mes
        estados_pago = {}
        for estado in estados_mensuales:
            key = estado["mes"]
            estados_pago[key] = "pagado" if estado["saldo"] >= 0 else "pendiente"
        
        return templates.TemplateResponse("propietario/mis_pagos.html", {
            "request": request,
            "propietario": propietario,
            "apartamento": apartamento,
            "estados_mensuales": estados_mensuales,
            "reporte_enviado": reporte_enviado,
            "concepto_cuota": concepto_cuota,
            "saldo_total": saldo_total,
            "total_cargos": total_cargos_general,
            "total_abonos": total_abonos_general,
            "estados_pago": estados_pago
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
            tipo_movimiento=TipoMovimientoEnum.CREDITO.value,
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
