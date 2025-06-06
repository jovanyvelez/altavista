from fastapi import APIRouter, Request, Form, HTTPException, status, Depends, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select, func
from typing import Optional, List
from datetime import datetime, date
from app.models import (
    db_manager, Usuario, Propietario, Apartamento, Concepto,
    PresupuestoAnual, RolUsuarioEnum, TipoMovimientoEnum,
    RegistroFinancieroApartamento, ItemPresupuesto, TipoItemPresupuestoEnum
)
from app.dependencies import templates, require_admin, get_db_session
from app.utils import guardar_documento

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Dashboard del administrador"""
    with get_db_session() as session:
        # Estadísticas básicas
        total_propietarios = session.exec(
            select(func.count(Propietario.id))
        ).first() or 0
        
        total_apartamentos = session.exec(
            select(func.count(Apartamento.id))
        ).first() or 0
        
        apartamentos_ocupados = session.exec(
            select(func.count(Apartamento.id)).where(Apartamento.propietario_id.isnot(None))
        ).first() or 0
        
        apartamentos_sin_propietario = total_apartamentos - apartamentos_ocupados
        
        # Registros financieros del mes actual
        mes_actual = datetime.now().month
        año_actual = datetime.now().year
        
        total_ingresos = session.exec(
            select(func.sum(RegistroFinancieroApartamento.monto))
            .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.CREDITO)
            .where(RegistroFinancieroApartamento.mes_aplicable == mes_actual)
            .where(RegistroFinancieroApartamento.año_aplicable == año_actual)
        ).first() or 0
        
        # Crear objeto stats con todas las estadísticas que necesita el template
        stats = {
            "total_apartamentos": total_apartamentos,
            "total_propietarios": total_propietarios,
            "apartamentos_sin_propietario": apartamentos_sin_propietario,
            "fecha_actual": datetime.now().strftime("%d/%m/%Y")
        }
        
        return templates.TemplateResponse("admin/dashboard.html", {
            "request": request,
            "stats": stats,
            "apartamentos_ocupados": apartamentos_ocupados,
            "porcentaje_ocupacion": round((apartamentos_ocupados / total_apartamentos * 100) if total_apartamentos > 0 else 0, 1),
            "total_ingresos": total_ingresos
        })

@router.get("/propietarios", response_class=HTMLResponse)
async def admin_propietarios(request: Request):
    """Lista de propietarios"""
    with get_db_session() as session:
        # Obtener todos los propietarios con sus apartamentos
        propietarios = session.exec(select(Propietario)).all()
        apartamentos = session.exec(select(Apartamento)).all()
        usuarios = session.exec(select(Usuario)).all()
        
        return templates.TemplateResponse("admin/propietarios.html", {
            "request": request,
            "propietarios": propietarios,
            "apartamentos": apartamentos,
            "usuarios": usuarios
        })

@router.get("/apartamentos", response_class=HTMLResponse) 
async def admin_apartamentos(request: Request):
    """Lista de apartamentos"""
    with get_db_session() as session:
        # Obtener apartamentos con información de propietarios
        apartamentos = session.exec(
            select(Apartamento)
        ).all()
        
        propietarios = session.exec(select(Propietario)).all()
        
        return templates.TemplateResponse("admin/apartamentos.html", {
            "request": request,
            "apartamentos": apartamentos,
            "propietarios": propietarios
        })

@router.get("/finanzas", response_class=HTMLResponse)
async def admin_finanzas(request: Request):
    """Vista de finanzas"""
    with get_db_session() as session:
        # Obtener apartamentos y conceptos para los formularios
        apartamentos = session.exec(select(Apartamento)).all()
        conceptos = session.exec(select(Concepto)).all()
        
        # Obtener registros financieros recientes
        registros_recientes = session.exec(
            select(RegistroFinancieroApartamento)
            .order_by(RegistroFinancieroApartamento.fecha_efectiva.desc())
            .limit(10)
        ).all()
        
        return templates.TemplateResponse("admin/finanzas.html", {
            "request": request,
            "apartamentos": apartamentos,
            "conceptos": conceptos,
            "registros_recientes": registros_recientes
        })

@router.post("/propietarios/crear")
async def crear_propietario(
    request: Request,
    nombre_completo: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(...),
    documento_identidad: str = Form(...),
    apartamento_id: Optional[int] = Form(None),
    username: str = Form(...),
    password: str = Form(...)
):
    """Crear nuevo propietario"""
    with get_db_session() as session:
        # Verificar que el username no exista
        usuario_existente = session.exec(
            select(Usuario).where(Usuario.username == username)
        ).first()
        
        if usuario_existente:
            return RedirectResponse(
                url="/admin/propietarios?error=username_exists",
                status_code=status.HTTP_302_FOUND
            )
        
        # Crear usuario
        nuevo_usuario = Usuario(
            username=username,
            password=password,
            nombre_completo=nombre_completo,
            email=email,
            rol=RolUsuarioEnum.PROPIETARIO
        )
        session.add(nuevo_usuario)
        session.commit()
        session.refresh(nuevo_usuario)
        
        # Crear propietario
        nuevo_propietario = Propietario(
            nombre_completo=nombre_completo,
            email=email,
            telefono=telefono,
            documento_identidad=documento_identidad,
            usuario_id=nuevo_usuario.id
        )
        session.add(nuevo_propietario)
        session.commit()
        session.refresh(nuevo_propietario)
        
        # Asignar apartamento si se especificó
        if apartamento_id:
            apartamento = session.get(Apartamento, apartamento_id)
            if apartamento and not apartamento.propietario_id:
                apartamento.propietario_id = nuevo_propietario.id
                session.add(apartamento)
                session.commit()
    
    return RedirectResponse(
        url="/admin/propietarios?success=1",
        status_code=status.HTTP_302_FOUND
    )

@router.post("/propietarios/{propietario_id}/editar")
async def editar_propietario(
    propietario_id: int,
    request: Request,
    nombre_completo: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(...),
    documento_identidad: str = Form(...),
    apartamento_id: Optional[int] = Form(None)
):
    """Editar propietario existente"""
    with get_db_session() as session:
        propietario = session.get(Propietario, propietario_id)
        if not propietario:
            raise HTTPException(status_code=404, detail="Propietario no encontrado")
        
        # Actualizar datos del propietario
        propietario.nombre_completo = nombre_completo
        propietario.email = email
        propietario.telefono = telefono
        propietario.documento_identidad = documento_identidad
        
        # Actualizar usuario asociado
        if propietario.usuario_id:
            usuario = session.get(Usuario, propietario.usuario_id)
            if usuario:
                usuario.nombre_completo = nombre_completo
                usuario.email = email
                session.add(usuario)
        
        # Manejar cambio de apartamento
        # Primero liberar apartamento anterior
        apartamento_anterior = session.exec(
            select(Apartamento).where(Apartamento.propietario_id == propietario_id)
        ).first()
        
        if apartamento_anterior:
            apartamento_anterior.propietario_id = None
            session.add(apartamento_anterior)
        
        # Asignar nuevo apartamento si se especificó
        if apartamento_id:
            apartamento = session.get(Apartamento, apartamento_id)
            if apartamento:
                apartamento.propietario_id = propietario_id
                session.add(apartamento)
        
        session.add(propietario)
        session.commit()
    
    return RedirectResponse(
        url="/admin/propietarios?updated=1",
        status_code=status.HTTP_302_FOUND
    )

@router.post("/propietarios/{propietario_id}/eliminar")
async def eliminar_propietario(propietario_id: int, request: Request):
    """Eliminar propietario"""
    with get_db_session() as session:
        propietario = session.get(Propietario, propietario_id)
        if not propietario:
            raise HTTPException(status_code=404, detail="Propietario no encontrado")
        
        # Verificar que no tenga registros financieros
        registros = session.exec(
            select(RegistroFinancieroApartamento)
            .join(Apartamento)
            .where(Apartamento.propietario_id == propietario_id)
        ).first()
        
        if registros:
            return RedirectResponse(
                url="/admin/propietarios?error=has_records",
                status_code=status.HTTP_302_FOUND
            )
        
        # Liberar apartamento
        apartamento = session.exec(
            select(Apartamento).where(Apartamento.propietario_id == propietario_id)
        ).first()
        
        if apartamento:
            apartamento.propietario_id = None
            session.add(apartamento)
        
        # Eliminar usuario asociado
        if propietario.usuario_id:
            usuario = session.get(Usuario, propietario.usuario_id)
            if usuario:
                session.delete(usuario)
        
        # Eliminar propietario
        session.delete(propietario)
        session.commit()
    
    return RedirectResponse(
        url="/admin/propietarios?deleted=1",
        status_code=status.HTTP_302_FOUND
    )

@router.post("/apartamentos/crear")
async def crear_apartamento(
    request: Request,
    numero: str = Form(...),
    piso: int = Form(...),
    propietario_id: Optional[int] = Form(None)
):
    """Crear nuevo apartamento"""
    with get_db_session() as session:
        # Verificar que el número no exista
        apartamento_existente = session.exec(
            select(Apartamento).where(Apartamento.numero == numero)
        ).first()
        
        if apartamento_existente:
            return RedirectResponse(
                url="/admin/apartamentos?error=numero_exists",
                status_code=status.HTTP_302_FOUND
            )
        
        # Crear apartamento
        nuevo_apartamento = Apartamento(
            numero=numero,
            piso=piso,
            propietario_id=propietario_id
        )
        session.add(nuevo_apartamento)
        session.commit()
    
    return RedirectResponse(
        url="/admin/apartamentos?success=1",
        status_code=status.HTTP_302_FOUND
    )

@router.post("/apartamentos/{apartamento_id}/editar")
async def editar_apartamento(
    apartamento_id: int,
    request: Request,
    numero: str = Form(...),
    piso: int = Form(...),
    propietario_id: Optional[int] = Form(None)
):
    """Editar apartamento existente"""
    with get_db_session() as session:
        apartamento = session.get(Apartamento, apartamento_id)
        if not apartamento:
            raise HTTPException(status_code=404, detail="Apartamento no encontrado")
        
        # Verificar que el número no exista en otro apartamento
        if numero != apartamento.numero:
            apartamento_existente = session.exec(
                select(Apartamento)
                .where(Apartamento.numero == numero)
                .where(Apartamento.id != apartamento_id)
            ).first()
            
            if apartamento_existente:
                return RedirectResponse(
                    url="/admin/apartamentos?error=numero_exists",
                    status_code=status.HTTP_302_FOUND
                )
        
        # Actualizar datos
        apartamento.numero = numero
        apartamento.piso = piso
        apartamento.propietario_id = propietario_id
        
        session.add(apartamento)
        session.commit()
    
    return RedirectResponse(
        url="/admin/apartamentos?updated=1",
        status_code=status.HTTP_302_FOUND
    )

@router.post("/apartamentos/{apartamento_id}/eliminar")
async def eliminar_apartamento(apartamento_id: int, request: Request):
    """Eliminar apartamento"""
    with get_db_session() as session:
        apartamento = session.get(Apartamento, apartamento_id)
        if not apartamento:
            raise HTTPException(status_code=404, detail="Apartamento no encontrado")
        
        # Verificar que no tenga registros financieros
        registros = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.apartamento_id == apartamento_id)
        ).first()
        
        if registros:
            return RedirectResponse(
                url="/admin/apartamentos?error=has_records",
                status_code=status.HTTP_302_FOUND
            )
        
        session.delete(apartamento)
        session.commit()
    
    return RedirectResponse(
        url="/admin/apartamentos?deleted=1",
        status_code=status.HTTP_302_FOUND
    )

@router.post("/conceptos/crear")
async def crear_concepto(
    request: Request,
    nombre: str = Form(...),
    es_ingreso_tipico: bool = Form(False)
):
    """Crear nuevo concepto"""
    with get_db_session() as session:
        nuevo_concepto = Concepto(
            nombre=nombre,
            es_ingreso_tipico=es_ingreso_tipico
        )
        session.add(nuevo_concepto)
        session.commit()
    
    return RedirectResponse(
        url="/admin/finanzas?success=1",
        status_code=status.HTTP_302_FOUND
    )

@router.post("/conceptos/{concepto_id}/eliminar")
async def eliminar_concepto(concepto_id: int, request: Request):
    """Eliminar concepto"""
    with get_db_session() as session:
        concepto = session.get(Concepto, concepto_id)
        if not concepto:
            raise HTTPException(status_code=404, detail="Concepto no encontrado")
        
        # Verificar que no tenga registros financieros
        registros = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.concepto_id == concepto_id)
        ).first()
        
        if registros:
            return RedirectResponse(
                url="/admin/finanzas?error=concepto_has_records",
                status_code=status.HTTP_302_FOUND
            )
        
        session.delete(concepto)
        session.commit()
    
    return RedirectResponse(
        url="/admin/finanzas?deleted=1",
        status_code=status.HTTP_302_FOUND
    )

@router.get("/registros-financieros/{apartamento_id}", response_class=HTMLResponse)
async def ver_registros_apartamento(apartamento_id: int, request: Request):
    """Ver registros financieros de un apartamento específico"""
    with get_db_session() as session:
        # Obtener apartamento
        apartamento = session.get(Apartamento, apartamento_id)
        if not apartamento:
            raise HTTPException(status_code=404, detail="Apartamento no encontrado")
        
        # Obtener registros financieros del apartamento
        registros = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.apartamento_id == apartamento_id)
            .order_by(RegistroFinancieroApartamento.fecha_efectiva.desc())
        ).all()
        
        # Obtener conceptos para el formulario
        conceptos = session.exec(select(Concepto)).all()
        
        # Calcular totales
        total_cargos = sum(
            r.monto for r in registros 
            if r.tipo_movimiento == TipoMovimientoEnum.DEBITO
        )
        total_abonos = sum(
            r.monto for r in registros 
            if r.tipo_movimiento == TipoMovimientoEnum.CREDITO
        )
        saldo = total_abonos - total_cargos
        
        return templates.TemplateResponse("admin/registros_financieros.html", {
            "request": request,
            "apartamento": apartamento,
            "registros": registros,
            "conceptos": conceptos,
            "total_cargos": total_cargos,
            "total_abonos": total_abonos,
            "saldo": saldo
        })

@router.post("/registros-financieros/crear")
async def crear_registro_financiero(
    request: Request,
    apartamento_id: int = Form(...),
    concepto_id: int = Form(...),
    tipo_movimiento: TipoMovimientoEnum = Form(...),
    monto: float = Form(...),
    fecha_efectiva: date = Form(...),
    mes_aplicable: int = Form(...),
    año_aplicable: int = Form(...),
    referencia_pago: Optional[str] = Form(None),
    descripcion_adicional: Optional[str] = Form(None),
    documento_soporte: Optional[UploadFile] = File(None)
):
    """Crear nuevo registro financiero"""
    ruta_documento = None
    if documento_soporte and documento_soporte.filename:
        ruta_documento = guardar_documento(documento_soporte, "registros_financieros")
    
    with get_db_session() as session:
        nuevo_registro = RegistroFinancieroApartamento(
            apartamento_id=apartamento_id,
            concepto_id=concepto_id,
            tipo_movimiento=tipo_movimiento,
            monto=monto,
            fecha_efectiva=fecha_efectiva,
            mes_aplicable=mes_aplicable,
            año_aplicable=año_aplicable,
            referencia_pago=referencia_pago,
            descripcion_adicional=descripcion_adicional,
            ruta_documento_soporte=ruta_documento,
            fecha_creacion=datetime.now()
        )
        session.add(nuevo_registro)
        session.commit()
    
    return RedirectResponse(
        url=f"/admin/registros-financieros/{apartamento_id}?success=1",
        status_code=status.HTTP_302_FOUND
    )

@router.post("/registros-financieros/{registro_id}/eliminar")
async def eliminar_registro_financiero(registro_id: int, request: Request):
    """Eliminar registro financiero"""
    with get_db_session() as session:
        registro = session.get(RegistroFinancieroApartamento, registro_id)
        if not registro:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        
        apartamento_id = registro.apartamento_id
        session.delete(registro)
        session.commit()
    
    return RedirectResponse(
        url=f"/admin/registros-financieros/{apartamento_id}?deleted=1",
        status_code=status.HTTP_302_FOUND
    )
