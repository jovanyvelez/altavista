from fastapi import FastAPI, Request, Depends, HTTPException, Form, status, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from typing import Optional
import uvicorn
from datetime import datetime, date
import os
import shutil
from pathlib import Path
from uuid import uuid4

# Importar modelos y utilidades
from app.models import (
    db_manager, Propietario, Apartamento, Usuario, Concepto,
    PresupuestoAnual, RolUsuarioEnum, TipoMovimientoEnum, RegistroFinancieroApartamento,
    ItemPresupuesto, TipoItemPresupuestoEnum, CuotaConfiguracion
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

# SISTEMA DE PAGOS PARA CUOTAS ORDINARIAS
@app.get("/admin/pagos", response_class=HTMLResponse)
async def admin_pagos(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Dashboard principal del sistema de pagos"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Obtener estadísticas del mes actual
    año_actual = datetime.now().year
    mes_actual = datetime.now().month
    
    # Obtener apartamentos y sus configuraciones de cuota
    apartamentos = session.exec(select(Apartamento)).all()
    total_apartamentos = len(apartamentos)
    
    # Obtener configuraciones de cuota para el mes actual
    configuraciones = session.exec(
        select(CuotaConfiguracion)
        .where(CuotaConfiguracion.año == año_actual)
        .where(CuotaConfiguracion.mes == mes_actual)
    ).all()
    
    apartamentos_configurados = len(configuraciones)
    
    # Calcular total a recaudar este mes
    total_a_recaudar = sum(config.monto_cuota_ordinaria_mensual for config in configuraciones)
    
    # Obtener concepto de cuota ordinaria
    concepto_cuota = session.exec(
        select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%"))
    ).first()
    
    # Obtener pagos realizados este mes
    pagos_mes = []
    total_recaudado = 0
    apartamentos_con_cargo = 0
    apartamentos_pagados = 0
    
    if concepto_cuota:
        # Cargos generados este mes
        cargos_mes = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id)
            .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.CARGO)
            .where(RegistroFinancieroApartamento.mes_aplicable == mes_actual)
            .where(RegistroFinancieroApartamento.año_aplicable == año_actual)
        ).all()
        apartamentos_con_cargo = len(cargos_mes)
        
        # Pagos realizados este mes
        pagos_mes = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id)
            .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.ABONO)
            .where(RegistroFinancieroApartamento.mes_aplicable == mes_actual)
            .where(RegistroFinancieroApartamento.año_aplicable == año_actual)
        ).all()
        total_recaudado = sum(pago.monto for pago in pagos_mes)
        apartamentos_pagados = len(set(pago.apartamento_id for pago in pagos_mes))
    
    # Calcular estadísticas
    porcentaje_recaudado = (total_recaudado / total_a_recaudar * 100) if total_a_recaudar > 0 else 0
    apartamentos_pendientes = apartamentos_con_cargo - apartamentos_pagados
    
    # Obtener apartamentos con saldos pendientes
    apartamentos_morosos = []
    for apartamento in apartamentos:
        registros = session.exec(
            select(RegistroFinancieroApartamento)
            .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
        ).all()
        
        if concepto_cuota:
            cargos = sum(r.monto for r in registros if r.tipo_movimiento == TipoMovimientoEnum.CARGO and r.concepto_id == concepto_cuota.id)
            abonos = sum(r.monto for r in registros if r.tipo_movimiento == TipoMovimientoEnum.ABONO and r.concepto_id == concepto_cuota.id)
            saldo = cargos - abonos
            
            if saldo > 0:
                apartamentos_morosos.append({
                    "apartamento": apartamento,
                    "saldo": saldo,
                    "meses_mora": 0  # Calcular meses en mora
                })
    
    return templates.TemplateResponse(
        "admin/pagos.html",
        {
            "request": request,
            "user": current_user,
            "año_actual": año_actual,
            "mes_actual": mes_actual,
            "total_apartamentos": total_apartamentos,
            "apartamentos_configurados": apartamentos_configurados,
            "apartamentos_con_cargo": apartamentos_con_cargo,
            "apartamentos_pagados": apartamentos_pagados,
            "apartamentos_pendientes": apartamentos_pendientes,
            "total_a_recaudar": total_a_recaudar,
            "total_recaudado": total_recaudado,
            "porcentaje_recaudado": porcentaje_recaudado,
            "apartamentos_morosos": apartamentos_morosos[:10],  # Solo los primeros 10
            "concepto_cuota": concepto_cuota
        }
    )

@app.get("/admin/pagos/configuracion", response_class=HTMLResponse)
async def admin_pagos_configuracion(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Configuración de cuotas ordinarias por apartamento"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Obtener apartamentos
    apartamentos = session.exec(select(Apartamento)).all()
    
    # Obtener configuraciones actuales
    año_actual = datetime.now().year
    configuraciones = {}
    
    for mes in range(1, 13):  # Enero a Diciembre
        configs_mes = session.exec(
            select(CuotaConfiguracion)
            .where(CuotaConfiguracion.año == año_actual)
            .where(CuotaConfiguracion.mes == mes)
        ).all()
        configuraciones[mes] = {config.apartamento_id: config for config in configs_mes}
    
    return templates.TemplateResponse(
        "admin/pagos_configuracion.html",
        {
            "request": request,
            "user": current_user,
            "apartamentos": apartamentos,
            "año_actual": año_actual,
            "configuraciones": configuraciones,
            "meses": [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]
        }
    )

@app.post("/admin/pagos/configuracion/guardar")
async def guardar_configuracion_cuotas(
    request: Request,
    año: int = Form(...),
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Guardar configuración masiva de cuotas"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    form_data = await request.form()
    
    # Procesar datos del formulario
    for key, value in form_data.items():
        if key.startswith("cuota_") and value:
            try:
                # Formato: cuota_apartamento_id_mes
                parts = key.split("_")
                apartamento_id = int(parts[1])
                mes = int(parts[2])
                monto = float(value)
                
                # Verificar si ya existe una configuración
                config_existente = session.exec(
                    select(CuotaConfiguracion)
                    .where(CuotaConfiguracion.apartamento_id == apartamento_id)
                    .where(CuotaConfiguracion.año == año)
                    .where(CuotaConfiguracion.mes == mes)
                ).first()
                
                if config_existente:
                    config_existente.monto_cuota_ordinaria_mensual = monto
                else:
                    nueva_config = CuotaConfiguracion(
                        apartamento_id=apartamento_id,
                        año=año,
                        mes=mes,
                        monto_cuota_ordinaria_mensual=monto
                    )
                    session.add(nueva_config)
            except (ValueError, IndexError):
                continue
    
    session.commit()
    
    return RedirectResponse(
        url="/admin/pagos/configuracion?success=1",
        status_code=status.HTTP_302_FOUND
    )

@app.get("/admin/pagos/generar-cargos", response_class=HTMLResponse)
async def admin_generar_cargos(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Página para generar cargos automáticos de cuotas ordinarias"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Obtener conceptos de cuota ordinaria
    conceptos_cuota = session.exec(
        select(Concepto).where(Concepto.nombre.ilike("%cuota%"))
    ).all()
    
    return templates.TemplateResponse(
        "admin/pagos_generar_cargos.html",
        {
            "request": request,
            "user": current_user,
            "conceptos_cuota": conceptos_cuota,
            "año_actual": datetime.now().year,
            "mes_actual": datetime.now().month
        }
    )

@app.post("/admin/pagos/generar-cargos")
async def generar_cargos_automaticos(
    request: Request,
    año: int = Form(...),
    mes: int = Form(...),
    concepto_id: int = Form(...),
    sobrescribir: bool = Form(False),
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Generar cargos automáticos de cuotas ordinarias"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Validar concepto
    concepto = session.get(Concepto, concepto_id)
    if not concepto:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")
    
    # Obtener configuraciones de cuotas para el mes/año especificado
    configuraciones = session.exec(
        select(CuotaConfiguracion)
        .where(CuotaConfiguracion.año == año)
        .where(CuotaConfiguracion.mes == mes)
    ).all()
    
    if not configuraciones:
        return RedirectResponse(
            url="/admin/pagos/generar-cargos?error=no_config",
            status_code=status.HTTP_302_FOUND
        )
    
    cargos_generados = 0
    cargos_actualizados = 0
    errores = []
    
    for config in configuraciones:
        try:
            # Verificar si ya existe un cargo para este apartamento/mes/año
            cargo_existente = session.exec(
                select(RegistroFinancieroApartamento)
                .where(RegistroFinancieroApartamento.apartamento_id == config.apartamento_id)
                .where(RegistroFinancieroApartamento.concepto_id == concepto_id)
                .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.CARGO)
                .where(RegistroFinancieroApartamento.mes_aplicable == mes)
                .where(RegistroFinancieroApartamento.año_aplicable == año)
            ).first()
            
            if cargo_existente and not sobrescribir:
                continue
            elif cargo_existente and sobrescribir:
                cargo_existente.monto = config.monto_cuota_ordinaria_mensual
                cargo_existente.fecha_registro = datetime.utcnow()
                cargos_actualizados += 1
            else:
                # Crear nuevo cargo
                nuevo_cargo = RegistroFinancieroApartamento(
                    apartamento_id=config.apartamento_id,
                    concepto_id=concepto_id,
                    tipo_movimiento=TipoMovimientoEnum.CARGO,
                    monto=config.monto_cuota_ordinaria_mensual,
                    fecha_efectiva=date(año, mes, 1),
                    mes_aplicable=mes,
                    año_aplicable=año,
                    descripcion_adicional=f"Cuota ordinaria {['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'][mes]} {año}"
                )
                session.add(nuevo_cargo)
                cargos_generados += 1
                
        except Exception as e:
            errores.append(f"Apartamento {config.apartamento.identificador}: {str(e)}")
    
    session.commit()
    
    return RedirectResponse(
        url=f"/admin/pagos/generar-cargos?success=1&generados={cargos_generados}&actualizados={cargos_actualizados}",
        status_code=status.HTTP_302_FOUND
    )

@app.get("/admin/pagos/procesar", response_class=HTMLResponse)
async def admin_procesar_pagos(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Interface para procesar pagos de cuotas ordinarias"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Obtener apartamentos con saldos pendientes
    apartamentos = session.exec(select(Apartamento)).all()
    concepto_cuota = session.exec(
        select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%"))
    ).first()
    
    apartamentos_con_saldo = []
    
    for apartamento in apartamentos:
        if concepto_cuota:
            # Calcular saldo pendiente
            registros = session.exec(
                select(RegistroFinancieroApartamento)
                .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
                .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id)
            ).all()
            
            cargos = sum(r.monto for r in registros if r.tipo_movimiento == TipoMovimientoEnum.CARGO)
            abonos = sum(r.monto for r in registros if r.tipo_movimiento == TipoMovimientoEnum.ABONO)
            saldo = cargos - abonos
            
            if saldo > 0:
                # Obtener últimos cargos pendientes
                cargos_pendientes = []
                for registro in registros:
                    if registro.tipo_movimiento == TipoMovimientoEnum.CARGO:
                        # Verificar si tiene abono correspondiente
                        abono_correspondiente = any(
                            r.tipo_movimiento == TipoMovimientoEnum.ABONO and
                            r.mes_aplicable == registro.mes_aplicable and
                            r.año_aplicable == registro.año_aplicable
                            for r in registros
                        )
                        if not abono_correspondiente:
                            cargos_pendientes.append(registro)
                
                apartamentos_con_saldo.append({
                    "apartamento": apartamento,
                    "saldo_total": saldo,
                    "cargos_pendientes": sorted(cargos_pendientes, key=lambda x: (x.año_aplicable, x.mes_aplicable))
                })
    
    # Ordenar por saldo descendente
    apartamentos_con_saldo.sort(key=lambda x: x["saldo_total"], reverse=True)
    
    return templates.TemplateResponse(
        "admin/pagos_procesar.html",
        {
            "request": request,
            "user": current_user,
            "apartamentos_con_saldo": apartamentos_con_saldo,
            "concepto_cuota": concepto_cuota
        }
    )

@app.post("/admin/pagos/procesar")
async def procesar_pago_cuota(
    request: Request,
    apartamento_id: int = Form(...),
    concepto_id: int = Form(...),
    monto_pago: float = Form(...),
    fecha_pago: str = Form(...),
    mes_aplicable: int = Form(...),
    año_aplicable: int = Form(...),
    referencia_pago: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Procesar un pago de cuota ordinaria"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Validaciones
    apartamento = session.get(Apartamento, apartamento_id)
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    
    concepto = session.get(Concepto, concepto_id)
    if not concepto:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")
    
    # Crear registro de pago
    pago = RegistroFinancieroApartamento(
        apartamento_id=apartamento_id,
        concepto_id=concepto_id,
        tipo_movimiento=TipoMovimientoEnum.ABONO,
        monto=monto_pago,
        fecha_efectiva=datetime.strptime(fecha_pago, "%Y-%m-%d").date(),
        mes_aplicable=mes_aplicable,
        año_aplicable=año_aplicable,
        referencia_pago=referencia_pago,
        descripcion_adicional=descripcion or f"Pago cuota {['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'][mes_aplicable]} {año_aplicable}"
    )
    
    session.add(pago)
    session.commit()
    
    return RedirectResponse(
        url="/admin/pagos/procesar?success=1",
        status_code=status.HTTP_302_FOUND
    )

@app.get("/admin/pagos/reportes", response_class=HTMLResponse)
async def admin_pagos_reportes(
    request: Request,
    año: Optional[int] = None,
    mes: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Reportes y análisis del sistema de pagos"""
    if not current_user or current_user.rol != RolUsuarioEnum.administrador:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    año_actual = datetime.now().year
    año_filtro = año or año_actual
    mes_filtro = mes
    
    # Obtener concepto de cuota ordinaria
    concepto_cuota = session.exec(
        select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%"))
    ).first()
    
    # Análisis mensual del año
    analisis_mensual = []
    total_cargos_año = 0
    total_esperado_año = 0
    total_recaudado_año = 0
    total_pagos_año = 0
    
    monto_esperado_mensual = []
    monto_recaudado_mensual = []
    
    for mes_num in range(1, 13):
        cargos_generados = 0
        monto_esperado = 0
        pagos_recibidos = 0
        monto_recaudado = 0
        
        if concepto_cuota:
            # Configuraciones del mes
            configuraciones = session.exec(
                select(CuotaConfiguracion)
                .where(CuotaConfiguracion.año == año_filtro)
                .where(CuotaConfiguracion.mes == mes_num)
            ).all()
            
            monto_esperado = sum(config.monto_cuota_ordinaria_mensual for config in configuraciones)
            
            # Cargos generados
            cargos = session.exec(
                select(RegistroFinancieroApartamento)
                .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id)
                .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.CARGO)
                .where(RegistroFinancieroApartamento.mes_aplicable == mes_num)
                .where(RegistroFinancieroApartamento.año_aplicable == año_filtro)
            ).all()
            
            cargos_generados = len(cargos)
            
            # Pagos recibidos
            pagos = session.exec(
                select(RegistroFinancieroApartamento)
                .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id)
                .where(RegistroFinancieroApartamento.tipo_movimiento == TipoMovimientoEnum.ABONO)
                .where(RegistroFinancieroApartamento.mes_aplicable == mes_num)
                .where(RegistroFinancieroApartamento.año_aplicable == año_filtro)
            ).all()
            
            pagos_recibidos = len(pagos)
            monto_recaudado = sum(pago.monto for pago in pagos)
        
        porcentaje_recaudacion = (monto_recaudado / monto_esperado * 100) if monto_esperado > 0 else 0
        monto_pendiente = monto_esperado - monto_recaudado
        
        analisis_mensual.append({
            "mes": mes_num,
            "nombre_mes": ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][mes_num],
            "cargos_generados": cargos_generados,
            "monto_esperado": monto_esperado,
            "pagos_recibidos": pagos_recibidos,
            "monto_recaudado": monto_recaudado,
            "porcentaje_recaudacion": porcentaje_recaudacion,
            "monto_pendiente": monto_pendiente
        })
        
        # Acumular totales anuales
        total_cargos_año += cargos_generados
        total_esperado_año += monto_esperado
        total_pagos_año += pagos_recibidos
        total_recaudado_año += monto_recaudado
        
        # Datos para gráficos
        monto_esperado_mensual.append(monto_esperado)
        monto_recaudado_mensual.append(monto_recaudado)
    
    # Estadísticas generales
    porcentaje_recaudacion = (total_recaudado_año / total_esperado_año * 100) if total_esperado_año > 0 else 0
    total_pendiente = total_esperado_año - total_recaudado_año
    
    # Análisis de apartamentos por estado
    apartamentos = session.exec(select(Apartamento)).all()
    apartamentos_al_dia = 0
    apartamentos_en_mora = 0
    apartamentos_criticos = 0
    top_deudores = []
    
    if concepto_cuota:
        for apartamento in apartamentos:
            # Calcular saldo del apartamento
            registros = session.exec(
                select(RegistroFinancieroApartamento)
                .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
                .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id)
            ).all()
            
            cargos = sum(r.monto for r in registros if r.tipo_movimiento == TipoMovimientoEnum.CARGO)
            abonos = sum(r.monto for r in registros if r.tipo_movimiento == TipoMovimientoEnum.ABONO)
            saldo = cargos - abonos
            
            # Clasificar apartamento
            if saldo <= 0:
                apartamentos_al_dia += 1
            elif saldo <= 1000:
                apartamentos_en_mora += 1
            else:
                apartamentos_criticos += 1
            
            # Agregar a top deudores si tiene saldo
            if saldo > 0:
                # Calcular meses en mora (simplificado)
                meses_mora = max(1, int(saldo / 500))  # Estimación basada en cuota promedio
                
                # Obtener último pago
                ultimo_pago = None
                pagos_apartamento = [r for r in registros if r.tipo_movimiento == TipoMovimientoEnum.ABONO]
                if pagos_apartamento:
                    ultimo_pago = max(pagos_apartamento, key=lambda x: x.fecha_efectiva).fecha_efectiva
                
                top_deudores.append({
                    "apartamento": apartamento,
                    "deuda_total": saldo,
                    "meses_mora": meses_mora,
                    "ultimo_pago": ultimo_pago
                })
    
    # Ordenar top deudores
    top_deudores.sort(key=lambda x: x["deuda_total"], reverse=True)
    
    return templates.TemplateResponse(
        "admin/pagos_reportes.html",
        {
            "request": request,
            "user": current_user,
            "año_actual": año_actual,
            "mes_actual": datetime.now().month,
            "analisis_mensual": analisis_mensual,
            "total_cargos_año": total_cargos_año,
            "total_esperado_año": total_esperado_año,
            "total_recaudado_año": total_recaudado_año,
            "total_pagos_año": total_pagos_año,
            "total_pendiente": total_pendiente,
            "porcentaje_recaudacion": porcentaje_recaudacion,
            "apartamentos_al_dia": apartamentos_al_dia,
            "apartamentos_en_mora": apartamentos_en_mora,
            "apartamentos_criticos": apartamentos_criticos,
            "top_deudores": top_deudores[:10],
            "monto_esperado_mensual": monto_esperado_mensual,
            "monto_recaudado_mensual": monto_recaudado_mensual,
            "concepto_cuota": concepto_cuota
        }
    )

# ENDPOINTS PARA PROPIETARIOS - PAGOS
@app.get("/propietario/mis-pagos", response_class=HTMLResponse)
async def propietario_mis_pagos(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Vista de pagos para propietarios"""
    if not current_user or current_user.rol != RolUsuarioEnum.propietario_consulta:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    # Obtener el apartamento del propietario (asumiendo un apartamento por propietario)
    apartamento = session.exec(
        select(Apartamento).where(Apartamento.propietario_id == current_user.propietario_id)
    ).first()
    
    if not apartamento:
        raise HTTPException(status_code=404, detail="No se encontró apartamento asociado")
    
    # Obtener concepto de cuota ordinaria
    concepto_cuota = session.exec(
        select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%"))
    ).first()
    
    # Calcular saldo total
    registros_financieros = session.exec(
        select(RegistroFinancieroApartamento)
        .where(RegistroFinancieroApartamento.apartamento_id == apartamento.id)
        .where(RegistroFinancieroApartamento.concepto_id == concepto_cuota.id if concepto_cuota else False)
        .order_by(RegistroFinancieroApartamento.fecha_efectiva.desc())
    ).all()
    
    total_cargos = sum(r.monto for r in registros_financieros if r.tipo_movimiento == TipoMovimientoEnum.CARGO)
    total_abonos = sum(r.monto for r in registros_financieros if r.tipo_movimiento == TipoMovimientoEnum.ABONO)
    saldo_total = total_cargos - total_abonos
    
    # Obtener configuraciones de cuotas del año actual
    año_actual = datetime.now().year
    configuraciones_cuotas = {}
    
    for mes in range(1, 13):
        config = session.exec(
            select(CuotaConfiguracion)
            .where(CuotaConfiguracion.apartamento_id == apartamento.id)
            .where(CuotaConfiguracion.año == año_actual)
            .where(CuotaConfiguracion.mes == mes)
        ).first()
        
        if config:
            configuraciones_cuotas[mes] = config
    
    # Calcular estados de pago por mes
    estados_pago = {}
    periodos_pendientes = 0
    total_pagado_año = 0
    
    for mes in range(1, 13):
        # Verificar si hay cargo para este mes
        cargo_mes = any(
            r.tipo_movimiento == TipoMovimientoEnum.CARGO and 
            r.mes_aplicable == mes and 
            r.año_aplicable == año_actual
            for r in registros_financieros
        )
        
        # Verificar si hay pago para este mes
        pago_mes = any(
            r.tipo_movimiento == TipoMovimientoEnum.ABONO and 
            r.mes_aplicable == mes and 
            r.año_aplicable == año_actual
            for r in registros_financieros
        )
        
        if cargo_mes and pago_mes:
            estados_pago[mes] = 'pagado'
            # Sumar pagos del año
            pagos_mes = sum(
                r.monto for r in registros_financieros 
                if r.tipo_movimiento == TipoMovimientoEnum.ABONO and 
                r.mes_aplicable == mes and 
                r.año_aplicable == año_actual
            )
            total_pagado_año += pagos_mes
        elif cargo_mes:
            # Verificar si está vencido (simplificado)
            fecha_limite = datetime(año_actual, mes, 28)  # Asumiendo vencimiento el 28
            if datetime.now() > fecha_limite:
                estados_pago[mes] = 'vencido'
            else:
                estados_pago[mes] = 'pendiente'
            periodos_pendientes += 1
        else:
            estados_pago[mes] = 'no_generado'
    
    return templates.TemplateResponse(
        "propietario/mis_pagos.html",
        {
            "request": request,
            "user": current_user,
            "apartamento": apartamento,
            "registros_financieros": registros_financieros,
            "saldo_total": saldo_total,
            "total_cargos": total_cargos,
            "total_abonos": total_abonos,
            "total_pagado_año": total_pagado_año,
            "periodos_pendientes": periodos_pendientes,
            "configuraciones_cuotas": configuraciones_cuotas,
            "estados_pago": estados_pago,
            "concepto_cuota": concepto_cuota,
            "now": datetime.now
        }
    )

@app.post("/propietario/reportar-pago")
async def propietario_reportar_pago(
    request: Request,
    apartamento_id: int = Form(...),
    monto_reportado: float = Form(...),
    fecha_pago_reportado: str = Form(...),
    metodo_pago: str = Form(...),
    referencia_reportada: Optional[str] = Form(None),
    observaciones: Optional[str] = Form(None),
    current_user: Usuario = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Endpoint para que propietarios reporten pagos realizados"""
    if not current_user or current_user.rol != RolUsuarioEnum.propietario_consulta:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    # Verificar que el apartamento pertenece al propietario
    apartamento = session.get(Apartamento, apartamento_id)
    if not apartamento or apartamento.propietario_id != current_user.propietario_id:
        raise HTTPException(status_code=403, detail="No autorizado para este apartamento")
    
    # Crear un registro de reporte de pago (pendiente de validación)
    # Nota: En un sistema real, esto iría a una tabla de reportes pendientes
    # Por simplicidad, crearemos un registro con un estado especial
    
    concepto_cuota = session.exec(
        select(Concepto).where(Concepto.nombre.ilike("%cuota%ordinaria%"))
    ).first()
    
    if concepto_cuota:
        # Crear registro temporal/pendiente
        reporte_pago = RegistroFinancieroApartamento(
            apartamento_id=apartamento_id,
            concepto_id=concepto_cuota.id,
            tipo_movimiento=TipoMovimientoEnum.ABONO,
            monto=monto_reportado,
            fecha_efectiva=datetime.strptime(fecha_pago_reportado, "%Y-%m-%d").date(),
            mes_aplicable=datetime.now().month,
            año_aplicable=datetime.now().year,
            referencia_pago=f"REPORTE-{metodo_pago}: {referencia_reportada or 'Sin referencia'}",
            descripcion_adicional=f"PENDIENTE VALIDACIÓN - {observaciones or 'Pago reportado por propietario'}"
        )
        
        session.add(reporte_pago)
        session.commit()
    
    return RedirectResponse(
        url="/propietario/mis-pagos?reporte_enviado=1",
        status_code=status.HTTP_302_FOUND
    )

# FIN SISTEMA DE PAGOS PARA CUOTAS ORDINARIAS

