from fastapi import FastAPI, Request, Depends, HTTPException, Form, status, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from typing import Optional
import uvicorn
from datetime import datetime
import os
import shutil
from pathlib import Path
from uuid import uuid4

# Importar modelos y utilidades
from app.models import (
    db_manager, Propietario, Apartamento, Usuario, Concepto,
    PresupuestoAnual, RolUsuarioEnum, TipoMovimientoEnum, RegistroFinancieroApartamento,
    ItemPresupuesto, TipoItemPresupuestoEnum
)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Sistema de Gestión Edificio Residencial",
    description="Sistema para la administración de zonas comunes de edificios residenciales",
    version="0.1.0"
)

# Configurar archivos estáticos y plantillas
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Directorio para almacenar documentos
UPLOADS_DIR = Path("static/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Función para guardar documentos
def guardar_documento(archivo: UploadFile, carpeta: str = "") -> str:
    """
    Guarda un documento subido por el usuario y retorna la ruta relativa al archivo
    
    Args:
        archivo: Archivo subido por el usuario
        carpeta: Subcarpeta opcional donde guardar el archivo
    
    Returns:
        str: Ruta relativa al archivo guardado
    """
    # Crear directorio si no existe
    dir_path = UPLOADS_DIR / carpeta
    dir_path.mkdir(exist_ok=True)
    
    # Generar nombre único para el archivo
    filename = f"{uuid4()}_{archivo.filename}"
    file_path = dir_path / filename
    
    # Guardar el archivo
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
    
    # Retornar ruta relativa para guardar en la base de datos
    return str(Path(carpeta) / filename)

# Función para obtener la ruta absoluta de un documento
def obtener_ruta_documento(ruta_relativa: str) -> Path:
    """
    Convierte una ruta relativa almacenada en la base de datos a una ruta absoluta
    
    Args:
        ruta_relativa: Ruta relativa del archivo
    
    Returns:
        Path: Ruta absoluta al archivo
    """
    return UPLOADS_DIR / ruta_relativa

# Inicializar base de datos al arranque
@app.on_event("startup")
async def startup_event():
    """Crear tablas si no existen"""
    db_manager.create_tables()
    # Datos iniciales para testing - uncomment if needed
    await crear_datos_iniciales()

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
                Concepto(nombre="Cuota de Administración", es_ingreso_tipico=True),
                Concepto(nombre="Mantenimiento Ascensor", es_ingreso_tipico=False),
                Concepto(nombre="Servicios Públicos", es_ingreso_tipico=False),
                Concepto(nombre="Vigilancia", es_ingreso_tipico=False),
                Concepto(nombre="Aseo", es_ingreso_tipico=False),
            ]
            for concepto in conceptos:
                session.add(concepto)
            
            # Crear propietarios de ejemplo
            propietarios = [
                Propietario(
                    nombre_completo="María González",
                    documento_identidad="12345678",
                    email="maria.gonzalez@email.com",
                    telefono="555-0001"
                ),
                Propietario(
                    nombre_completo="Carlos Rodríguez",
                    documento_identidad="87654321",
                    email="carlos.rodriguez@email.com",
                    telefono="555-0002"
                )
            ]
            for propietario in propietarios:
                session.add(propietario)
            
            session.commit()
            session.refresh(propietarios[0])
            session.refresh(propietarios[1])
            
            # Crear apartamentos
            apartamentos = [
                Apartamento(
                    identificador="Apto 101",
                    coeficiente_copropiedad=0.012500,
                    propietario_id=propietarios[0].id
                ),
                Apartamento(
                    identificador="Apto 102",
                    coeficiente_copropiedad=0.012500,
                    propietario_id=propietarios[1].id
                ),
                Apartamento(
                    identificador="Apto 201",
                    coeficiente_copropiedad=0.012500
                )
            ]
            for apartamento in apartamentos:
                session.add(apartamento)
            
            # Crear usuarios
            usuarios = [
                Usuario(
                    username="admin",
                    email="admin@edificio.com",
                    hashed_password="admin123",  # En producción usar hash real
                    nombre_completo="Administrador del Edificio",
                    rol=RolUsuarioEnum.administrador
                ),
                Usuario(
                    username="maria.gonzalez",
                    email="maria.gonzalez@email.com",
                    hashed_password="password123",
                    nombre_completo="María González",
                    rol=RolUsuarioEnum.propietario_consulta,
                    propietario_id=propietarios[0].id
                )
            ]
            for usuario in usuarios:
                session.add(usuario)
            
            # Crear presupuesto anual
            presupuesto = PresupuestoAnual(
                año=2025,
                descripcion="Presupuesto anual 2025"
            )
            session.add(presupuesto)
            
            session.commit()

# Dependency para obtener sesión de base de datos
def get_session():
    with db_manager.get_session() as session:
        yield session

# Simulación de autenticación básica (en producción usar JWT)
def get_current_user(request: Request, session: Session = Depends(get_session)) -> Optional[Usuario]:
    username = request.session.get("username")
    if username:
        return session.exec(select(Usuario).where(Usuario.username == username)).first()
    return None

# RUTAS PRINCIPALES

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página de inicio con login"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    """Procesar login de usuario"""
    user = session.exec(
        select(Usuario).where(
            Usuario.username == username,
            Usuario.hashed_password == password,  # En producción verificar hash
            Usuario.is_active == True
        )
    ).first()
    
    if not user:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Credenciales inválidas"}
        )
    
    # Guardar usuario en sesión (en producción usar JWT)
    request.session["username"] = user.username
    
    # Redirigir según el rol
    if user.rol == RolUsuarioEnum.administrador:
        return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)
    else:
        return RedirectResponse(url="/propietario/dashboard", status_code=status.HTTP_302_FOUND)

@app.get("/logout")
async def logout(request: Request):
    """Cerrar sesión"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

# RUTAS DEL ADMINISTRADOR

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Dashboard principal del administrador"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    # Obtener estadísticas básicas
    total_apartamentos = len(session.exec(select(Apartamento)).all())
    total_propietarios = len(session.exec(select(Propietario)).all())
    apartamentos_sin_propietario = len(session.exec(
        select(Apartamento).where(Apartamento.propietario_id == None)
    ).all())
    
    stats = {
        "total_apartamentos": total_apartamentos,
        "total_propietarios": total_propietarios,
        "apartamentos_sin_propietario": apartamentos_sin_propietario,
        "fecha_actual": datetime.now().strftime("%d/%m/%Y")
    }
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "user": current_user, "stats": stats}
    )

@app.get("/admin/propietarios", response_class=HTMLResponse)
async def admin_propietarios(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Gestión de propietarios"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    propietarios = session.exec(select(Propietario)).all()
    
    return templates.TemplateResponse(
        "admin/propietarios.html",
        {"request": request, "user": current_user, "propietarios": propietarios}
    )

@app.get("/admin/apartamentos", response_class=HTMLResponse)
async def admin_apartamentos(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Gestión de apartamentos"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    apartamentos = session.exec(select(Apartamento)).all()
    propietarios = session.exec(select(Propietario)).all()
    
    return templates.TemplateResponse(
        "admin/apartamentos.html",
        {
            "request": request, 
            "user": current_user, 
            "apartamentos": apartamentos,
            "propietarios": propietarios
        }
    )

@app.get("/admin/finanzas", response_class=HTMLResponse)
async def admin_finanzas(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Gestión financiera"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    presupuestos = session.exec(select(PresupuestoAnual)).all()
    conceptos = session.exec(select(Concepto)).all()
    
    return templates.TemplateResponse(
        "admin/finanzas.html",
        {
            "request": request, 
            "user": current_user, 
            "presupuestos": presupuestos,
            "conceptos": conceptos,
            "now": datetime.now
        }
    )

# RUTAS DEL PROPIETARIO

@app.get("/propietario/dashboard", response_class=HTMLResponse)
async def propietario_dashboard(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Dashboard del propietario"""
    if not current_user or current_user.rol != RolUsuarioEnum.propietario_consulta:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    # Obtener apartamentos del propietario
    apartamentos = session.exec(
        select(Apartamento).where(Apartamento.propietario_id == current_user.propietario_id)
    ).all()
    
    return templates.TemplateResponse(
        "propietario/dashboard.html",
        {
            "request": request, 
            "user": current_user, 
            "apartamentos": apartamentos,
            "propietario": current_user.propietario
        }
    )

# ENDPOINTS CRUD PARA PROPIETARIOS

@app.post("/admin/propietarios/crear")
async def crear_propietario(
    request: Request,
    nombre_completo: str = Form(...),
    documento_identidad: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(...),
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Crear nuevo propietario"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Verificar si ya existe el documento
    propietario_existente = session.exec(
        select(Propietario).where(Propietario.documento_identidad == documento_identidad)
    ).first()
    
    if propietario_existente:
        return templates.TemplateResponse(
            "admin/propietarios.html",
            {
                "request": request,
                "user": current_user,
                "propietarios": session.exec(select(Propietario)).all(),
                "error": "Ya existe un propietario con ese documento"
            }
        )
    
    nuevo_propietario = Propietario(
        nombre_completo=nombre_completo,
        documento_identidad=documento_identidad,
        email=email,
        telefono=telefono
    )
    
    session.add(nuevo_propietario)
    session.commit()
    
    return RedirectResponse(url="/admin/propietarios", status_code=status.HTTP_302_FOUND)

@app.post("/admin/propietarios/{propietario_id}/editar")
async def editar_propietario(
    propietario_id: int,
    request: Request,
    nombre_completo: str = Form(...),
    documento_identidad: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(...),
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Editar propietario existente"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    propietario = session.get(Propietario, propietario_id)
    if not propietario:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")
    
    # Verificar si el documento no esté siendo usado por otro propietario
    propietario_existente = session.exec(
        select(Propietario).where(
            Propietario.documento_identidad == documento_identidad,
            Propietario.id != propietario_id
        )
    ).first()
    
    if propietario_existente:
        return templates.TemplateResponse(
            "admin/propietarios.html",
            {
                "request": request,
                "user": current_user,
                "propietarios": session.exec(select(Propietario)).all(),
                "error": "Ya existe otro propietario con ese documento"
            }
        )
    
    propietario.nombre_completo = nombre_completo
    propietario.documento_identidad = documento_identidad
    propietario.email = email
    propietario.telefono = telefono
    
    session.add(propietario)
    session.commit()
    
    return RedirectResponse(url="/admin/propietarios", status_code=status.HTTP_302_FOUND)

@app.post("/admin/propietarios/{propietario_id}/eliminar")
async def eliminar_propietario(
    propietario_id: int,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Eliminar propietario"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    propietario = session.get(Propietario, propietario_id)
    if not propietario:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")
    
    # Verificar si tiene apartamentos asignados
    apartamentos = session.exec(
        select(Apartamento).where(Apartamento.propietario_id == propietario_id)
    ).all()
    
    if apartamentos:
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar el propietario porque tiene apartamentos asignados"
        )
    
    session.delete(propietario)
    session.commit()
    
    return RedirectResponse(url="/admin/propietarios", status_code=status.HTTP_302_FOUND)

# ENDPOINTS CRUD PARA APARTAMENTOS

@app.post("/admin/apartamentos/crear")
async def crear_apartamento(
    request: Request,
    identificador: str = Form(...),
    coeficiente_copropiedad: float = Form(...),
    propietario_id: Optional[int] = Form(None),
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Crear nuevo apartamento"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Verificar si ya existe el identificador
    apartamento_existente = session.exec(
        select(Apartamento).where(Apartamento.identificador == identificador)
    ).first()
    
    if apartamento_existente:
        apartamentos = session.exec(select(Apartamento)).all()
        propietarios = session.exec(select(Propietario)).all()
        return templates.TemplateResponse(
            "admin/apartamentos.html",
            {
                "request": request,
                "user": current_user,
                "apartamentos": apartamentos,
                "propietarios": propietarios,
                "error": "Ya existe un apartamento con ese identificador"
            }
        )
    
    nuevo_apartamento = Apartamento(
        identificador=identificador,
        coeficiente_copropiedad=coeficiente_copropiedad,
        propietario_id=propietario_id if propietario_id else None
    )
    
    session.add(nuevo_apartamento)
    session.commit()
    
    return RedirectResponse(url="/admin/apartamentos", status_code=status.HTTP_302_FOUND)

@app.post("/admin/apartamentos/{apartamento_id}/editar")
async def editar_apartamento(
    apartamento_id: int,
    request: Request,
    identificador: str = Form(...),
    coeficiente_copropiedad: float = Form(...),
    propietario_id: Optional[int] = Form(None),
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Editar apartamento existente"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    apartamento = session.get(Apartamento, apartamento_id)
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    
    # Verificar si el identificador no esté siendo usado por otro apartamento
    apartamento_existente = session.exec(
        select(Apartamento).where(
            Apartamento.identificador == identificador,
            Apartamento.id != apartamento_id
        )
    ).first()
    
    if apartamento_existente:
        apartamentos = session.exec(select(Apartamento)).all()
        propietarios = session.exec(select(Propietario)).all()
        return templates.TemplateResponse(
            "admin/apartamentos.html",
            {
                "request": request,
                "user": current_user,
                "apartamentos": apartamentos,
                "propietarios": propietarios,
                "error": "Ya existe otro apartamento con ese identificador"
            }
        )
    
    apartamento.identificador = identificador
    apartamento.coeficiente_copropiedad = coeficiente_copropiedad
    apartamento.propietario_id = propietario_id if propietario_id else None
    
    session.add(apartamento)
    session.commit()
    
    return RedirectResponse(url="/admin/apartamentos", status_code=status.HTTP_302_FOUND)

@app.post("/admin/apartamentos/{apartamento_id}/eliminar")
async def eliminar_apartamento(
    apartamento_id: int,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Eliminar apartamento"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    apartamento = session.get(Apartamento, apartamento_id)
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    
    session.delete(apartamento)
    session.commit()
    
    return RedirectResponse(url="/admin/apartamentos", status_code=status.HTTP_302_FOUND)

# ENDPOINTS CRUD PARA CONCEPTOS

@app.post("/admin/conceptos/crear")
async def crear_concepto(
    request: Request,
    nombre: str = Form(...),
    es_ingreso_tipico: bool = Form(False),
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Crear nuevo concepto"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    nuevo_concepto = Concepto(
        nombre=nombre,
        es_ingreso_tipico=es_ingreso_tipico
    )
    
    session.add(nuevo_concepto)
    session.commit()
    
    return RedirectResponse(url="/admin/finanzas", status_code=status.HTTP_302_FOUND)

@app.post("/admin/conceptos/{concepto_id}/eliminar")
async def eliminar_concepto(
    concepto_id: int,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Eliminar concepto"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    concepto = session.get(Concepto, concepto_id)
    if not concepto:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")
    
    session.delete(concepto)
    session.commit()
    
    return RedirectResponse(url="/admin/finanzas", status_code=status.HTTP_302_FOUND)

# ENDPOINTS PARA REGISTROS FINANCIEROS

@app.get("/admin/registros-financieros/{apartamento_id}", response_class=HTMLResponse)
async def admin_registros_financieros(
    apartamento_id: int,
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Ver registros financieros de un apartamento"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    apartamento = session.get(Apartamento, apartamento_id)
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    
    # Obtener conceptos para el formulario
    conceptos = session.exec(select(Concepto)).all()
    
    # Obtener registros financieros
    registros = session.exec(
        select(RegistroFinancieroApartamento)
        .where(RegistroFinancieroApartamento.apartamento_id == apartamento_id)
        .order_by(RegistroFinancieroApartamento.fecha_registro.desc())
    ).all()
    
    # Calcular saldos
    total_cargos = sum(reg.monto for reg in registros if reg.tipo_movimiento == TipoMovimientoEnum.CARGO)
    total_abonos = sum(reg.monto for reg in registros if reg.tipo_movimiento == TipoMovimientoEnum.ABONO)
    saldo_total = total_cargos - total_abonos
    
    return templates.TemplateResponse(
        "admin/registros_financieros.html",
        {
            "request": request,
            "user": current_user,
            "apartamento": apartamento,
            "registros": registros,
            "conceptos": conceptos,
            "total_cargos": total_cargos,
            "total_abonos": total_abonos,
            "saldo_total": saldo_total,
            "now": datetime.now
        }
    )

@app.post("/admin/registros-financieros/crear")
async def crear_registro_financiero(
    request: Request,
    apartamento_id: int = Form(...),
    concepto_id: int = Form(...),
    tipo_movimiento: str = Form(...),
    monto: float = Form(...),
    fecha_efectiva: str = Form(...),
    descripcion_adicional: Optional[str] = Form(None),
    mes_aplicable: Optional[int] = Form(None),
    año_aplicable: Optional[int] = Form(None),
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Crear nuevo registro financiero"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    apartamento = session.get(Apartamento, apartamento_id)
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    
    concepto = session.get(Concepto, concepto_id)
    if not concepto:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")
    
    tipo_enum = TipoMovimientoEnum.CARGO if tipo_movimiento == "cargo" else TipoMovimientoEnum.ABONO
    
    registro = RegistroFinancieroApartamento(
        apartamento_id=apartamento_id,
        concepto_id=concepto_id,
        tipo_movimiento=tipo_enum,
        monto=monto,
        fecha_efectiva=datetime.strptime(fecha_efectiva, "%Y-%m-%d").date(),
        descripcion_adicional=descripcion_adicional,
        mes_aplicable=mes_aplicable,
        año_aplicable=año_aplicable
    )
    
    session.add(registro)
    session.commit()
    
    return RedirectResponse(
        url=f"/admin/registros-financieros/{apartamento_id}",
        status_code=status.HTTP_302_FOUND
    )

@app.post("/admin/registros-financieros/{registro_id}/eliminar")
async def eliminar_registro_financiero(
    registro_id: int,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Eliminar registro financiero"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    registro = session.get(RegistroFinancieroApartamento, registro_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    
    apartamento_id = registro.apartamento_id
    
    session.delete(registro)
    session.commit()
    
    return RedirectResponse(
        url=f"/admin/registros-financieros/{apartamento_id}",
        status_code=status.HTTP_302_FOUND
    )

@app.get("/propietario/estado-cuenta", response_class=HTMLResponse)
async def propietario_estado_cuenta(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Estado de cuenta del propietario"""
    if not current_user or current_user.rol != RolUsuarioEnum.propietario_consulta:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    # Obtener apartamentos del propietario
    apartamentos = session.exec(
        select(Apartamento).where(Apartamento.propietario_id == current_user.propietario_id)
    ).all()
    
    # Obtener registros financieros de todos los apartamentos del propietario
    todos_registros = []
    saldos_por_apartamento = {}
    
    for apartamento in apartamentos:
        registros = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
            .order_by(RegistroFinancieroApartamento.fecha_registro.desc())
        ).all()
        
        todos_registros.extend(registros)
        
        # Calcular saldo para este apartamento
        cargos = sum(reg.monto for reg in registros if reg.tipo_movimiento == TipoMovimientoEnum.CARGO)
        abonos = sum(reg.monto for reg in registros if reg.tipo_movimiento == TipoMovimientoEnum.ABONO)
        saldo = cargos - abonos
        
        saldos_por_apartamento[apartamento.id] = {
            "apartamento": apartamento,
            "cargos": cargos,
            "abonos": abonos,
            "saldo": saldo
        }
    
    # Ordenar registros por fecha
    todos_registros.sort(key=lambda x: x.fecha_registro, reverse=True)
    
    # Calcular totales generales
    total_cargos = sum(reg.monto for reg in todos_registros if reg.tipo_movimiento == TipoMovimientoEnum.CARGO)
    total_abonos = sum(reg.monto for reg in todos_registros if reg.tipo_movimiento == TipoMovimientoEnum.ABONO)
    saldo_total = total_cargos - total_abonos
    
    return templates.TemplateResponse(
        "propietario/estado_cuenta.html",
        {
            "request": request, 
            "user": current_user,
            "apartamentos": apartamentos,
            "registros": todos_registros,
            "saldos_por_apartamento": saldos_por_apartamento,
            "total_cargos": total_cargos,
            "total_abonos": total_abonos,
            "saldo_total": saldo_total
        }
    )

# ENDPOINTS CRUD PARA PRESUPUESTOS ANUALES

@app.get("/admin/presupuestos", response_class=HTMLResponse)
async def admin_presupuestos(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Listar todos los presupuestos anuales"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Obtener todos los presupuestos con sus estadísticas
    presupuestos = session.exec(select(PresupuestoAnual).order_by(PresupuestoAnual.año.desc())).all()
    
    # Calcular estadísticas para cada presupuesto
    presupuestos_con_stats = []
    for presupuesto in presupuestos:
        items = session.exec(
            select(ItemPresupuesto).where(ItemPresupuesto.presupuesto_anual_id == presupuesto.id)
        ).all()
        
        total_ingresos = sum(item.monto_presupuestado for item in items if item.tipo_item == TipoItemPresupuestoEnum.INGRESO)
        total_gastos = sum(item.monto_presupuestado for item in items if item.tipo_item == TipoItemPresupuestoEnum.GASTO)
        balance = total_ingresos - total_gastos
        
        presupuestos_con_stats.append({
            "presupuesto": presupuesto,
            "total_ingresos": total_ingresos,
            "total_gastos": total_gastos,
            "balance": balance
        })
    
    # Obtener conceptos para el formulario de nuevo presupuesto
    conceptos = session.exec(select(Concepto)).all()
    
    return templates.TemplateResponse(
        "admin/presupuestos.html",
        {
            "request": request,
            "user": current_user,
            "presupuestos_con_stats": presupuestos_con_stats,
            "conceptos": conceptos,
            "now": datetime.now
        }
    )

@app.post("/admin/presupuestos/crear")
async def crear_presupuesto(
    request: Request,
    año: int = Form(...),
    descripcion: str = Form(...),
    redirect_to: str = Form("/admin/finanzas"),
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Crear nuevo presupuesto anual"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Verificar si ya existe un presupuesto para ese año
    presupuesto_existente = session.exec(
        select(PresupuestoAnual).where(PresupuestoAnual.año == año)
    ).first()
    
    if presupuesto_existente:
        return templates.TemplateResponse(
            "admin/finanzas.html",
            {
                "request": request,
                "user": current_user,
                "presupuestos": session.exec(select(PresupuestoAnual)).all(),
                "conceptos": session.exec(select(Concepto)).all(),
                "error": f"Ya existe un presupuesto para el año {año}"
            }
        )
    
    nuevo_presupuesto = PresupuestoAnual(
        año=año,
        descripcion=descripcion
    )
    
    session.add(nuevo_presupuesto)
    session.commit()
    
    return RedirectResponse(url=redirect_to, status_code=status.HTTP_302_FOUND)

@app.get("/admin/presupuestos/{presupuesto_id}", response_class=HTMLResponse)
async def ver_presupuesto(
    presupuesto_id: int,
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Ver detalle de un presupuesto anual"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    presupuesto = session.get(PresupuestoAnual, presupuesto_id)
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    
    # Obtener conceptos para el formulario de nuevos items
    conceptos = session.exec(select(Concepto)).all()
    
    # Obtener items del presupuesto
    items = session.exec(
        select(ItemPresupuesto).where(ItemPresupuesto.presupuesto_anual_id == presupuesto_id)
    ).all()
    total_ingresos = sum(item.monto_presupuestado for item in items if item.tipo_item == TipoItemPresupuestoEnum.INGRESO)
    total_gastos = sum(item.monto_presupuestado for item in items if item.tipo_item == TipoItemPresupuestoEnum.GASTO)
    balance = total_ingresos - total_gastos
    
    return templates.TemplateResponse(
        "admin/presupuesto_detalle.html",
        {
            "request": request,
            "user": current_user,
            "presupuesto": presupuesto,
            "items": items,
            "conceptos": conceptos,
            "total_ingresos": total_ingresos,
            "total_gastos": total_gastos,
            "balance": balance
        }
    )

@app.post("/admin/presupuestos/{presupuesto_id}/items/crear")
async def crear_item_presupuesto(
    presupuesto_id: int,
    request: Request,
    concepto_id: int = Form(...),
    tipo: str = Form(...),
    monto: float = Form(...),
    mes: int = Form(1),
    descripcion: Optional[str] = Form(None),
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Crear nuevo item de presupuesto"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    presupuesto = session.get(PresupuestoAnual, presupuesto_id)
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    
    tipo_enum = TipoItemPresupuestoEnum.INGRESO if tipo == "ingreso" else TipoItemPresupuestoEnum.GASTO
    
    nuevo_item = ItemPresupuesto(
        presupuesto_anual_id=presupuesto_id,
        concepto_id=concepto_id,
        tipo_item=tipo_enum,
        monto_presupuestado=monto,
        mes=mes,
        descripcion=descripcion
    )
    
    session.add(nuevo_item)
    session.commit()
    
    return RedirectResponse(
        url=f"/admin/presupuestos/{presupuesto_id}", 
        status_code=status.HTTP_302_FOUND
    )

@app.post("/admin/presupuestos/{presupuesto_id}/items/{item_id}/eliminar")
async def eliminar_item_presupuesto(
    presupuesto_id: int,
    item_id: int,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Eliminar item de presupuesto"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    item = session.get(ItemPresupuesto, item_id)
    if not item or item.presupuesto_anual_id != presupuesto_id:
        raise HTTPException(status_code=404, detail="Item de presupuesto no encontrado")
    
    session.delete(item)
    session.commit()
    
    return RedirectResponse(
        url=f"/admin/presupuestos/{presupuesto_id}", 
        status_code=status.HTTP_302_FOUND
    )

# Endpoints para manejo de documentos

@app.post("/admin/documentos/subir")
async def subir_documento(
    request: Request,
    documento: UploadFile = File(...),
    tipo_documento: str = Form(...),
    entidad_id: int = Form(...),
    descripcion: Optional[str] = Form(None),
    current_user: Usuario = Depends(get_current_user)
):
    """Subir un documento al sistema"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Verificar extensión de archivo permitida
    extensiones_permitidas = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
    ext = Path(documento.filename).suffix.lower()
    
    if ext not in extensiones_permitidas:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de archivo no permitido. Use: {', '.join(extensiones_permitidas)}"
        )
    
    # Guardar documento
    ruta_documento = guardar_documento(documento, f"{tipo_documento}/{entidad_id}")
    
    # En un sistema real, aquí guardaríamos la información del documento en la base de datos
    
    return {"success": True, "ruta_documento": ruta_documento}

# Configuración de sesiones
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key="tu-clave-secreta-muy-segura")





@app.get("/admin/presupuestos1/{presupuesto_id}")
async def ver_presupuesto(
    presupuesto_id: int,
    request: Request,
    session: Session = Depends(get_session)
):
    
    presupuesto = session.get(PresupuestoAnual, presupuesto_id)
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    
    # Obtener conceptos para el formulario de nuevos items
    conceptos = session.exec(select(Concepto)).all()

    # Obtener items del presupuesto
    items = session.exec(
        select(ItemPresupuesto).where(ItemPresupuesto.presupuesto_anual_id == presupuesto_id)
    ).all()


    total_ingresos = sum(item.monto_presupuestado for item in items if item.tipo_item == TipoItemPresupuestoEnum.INGRESO)
    total_gastos = sum(item.monto_presupuestado for item in items if item.tipo_item == TipoItemPresupuestoEnum.GASTO)
    balance = total_ingresos - total_gastos
    
    return {"presupuesto": presupuesto}
    
    