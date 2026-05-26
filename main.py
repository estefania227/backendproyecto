from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

# === BACKEND CLARO Y ACADÉMICO ===
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENUMS (Roles y Estados) ---
class RolEnum(str, Enum):
    ADMIN = "ADMIN"
    SCIENTIST = "SCIENTIST"
    OPERATOR = "OPERATOR"

class EstadoOrdenEnum(str, Enum):
    BORRADOR = "BORRADOR"
    APROBADA = "APROBADA"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"

# --- MODELOS (Pydantic) ---
class Usuario(BaseModel):
    username: str
    password: str
    rol: Optional[RolEnum] = RolEnum.OPERATOR

class UsuarioResponse(BaseModel):
    id: int
    username: str
    rol: RolEnum
    activo: bool

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    ok: bool
    token: Optional[str] = None
    usuario: Optional[UsuarioResponse] = None
    message: Optional[str] = None

class Reactivo(BaseModel):
    nombre: str
    stock: int
    vencimiento: str
    unidadMedida: str = "ml"
    proveedor: str = "Sin especificar"

class Equipo(BaseModel):
    nombre: str
    estado: str = "DISPONIBLE"

class Nanomaterial(BaseModel):
    nombre: str
    descripcion: str

class Orden(BaseModel):
    nanomaterial: str
    reactivos: List[str]
    equipo: str
    observaciones: str = ""

# --- BASE DE DATOS EN MEMORIA ---
usuarios_db = [
    {"id": 1, "username": "admin", "password": "1234", "rol": "ADMIN", "activo": True},
    {"id": 2, "username": "cientifico1", "password": "1234", "rol": "SCIENTIST", "activo": True},
    {"id": 3, "username": "operador1", "password": "1234", "rol": "OPERATOR", "activo": True}
]
sesiones_activas = {}
reactivos = [
    {"id": 1, "nombre": "Ácido clorhídrico", "stock": 20, "vencimiento": "2026-12-31", "unidadMedida": "ml", "proveedor": "ChemCorp"}
]
equipos = [
    {"id": 1, "nombre": "Microscopio", "estado": "DISPONIBLE"}
]
nanomateriales = [
    {"id": 1, "nombre": "Nanooro", "descripcion": "Nanopartículas de oro"}
]
ordenes = []

# --- AUTENTICACIÓN ---
def generar_token(username: str) -> str:
    import secrets
    token = secrets.token_urlsafe(32)
    sesiones_activas[token] = username
    return token

def validar_token(token: str) -> dict:
    if token not in sesiones_activas:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    username = sesiones_activas[token]
    usuario = next((u for u in usuarios_db if u["username"] == username), None)
    if not usuario or not usuario["activo"]:
        raise HTTPException(status_code=401, detail="Usuario inactivo")
    return usuario

def obtener_usuario_actual(token: str = None) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido")
    return validar_token(token)

def validar_admin(usuario: dict):
    if usuario["rol"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Solo administradores pueden hacer esto")

# --- ENDPOINTS DE AUTENTICACIÓN ---
@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    usuario = next((u for u in usuarios_db if u["username"] == request.username), None)
    if not usuario or usuario["password"] != request.password:
        return LoginResponse(ok=False, message="Usuario o contraseña incorrectos")
    if not usuario["activo"]:
        return LoginResponse(ok=False, message="Usuario inactivo")
    token = generar_token(usuario["username"])
    return LoginResponse(
        ok=True,
        token=token,
        usuario=UsuarioResponse(
            id=usuario["id"],
            username=usuario["username"],
            rol=usuario["rol"],
            activo=usuario["activo"]
        )
    )

@app.post("/logout")
def logout(token: str = None):
    if token and token in sesiones_activas:
        del sesiones_activas[token]
    return {"message": "Sesión cerrada"}

@app.get("/me")
def obtener_usuario_autenticado(token: str = None):
    usuario = obtener_usuario_actual(token)
    return UsuarioResponse(
        id=usuario["id"],
        username=usuario["username"],
        rol=usuario["rol"],
        activo=usuario["activo"]
    )

# --- ENDPOINTS DE USUARIOS (Solo ADMIN) ---
@app.get("/usuarios")
def listar_usuarios(token: str = None):
    usuario = obtener_usuario_actual(token)
    validar_admin(usuario)
    return [
        {"id": u["id"], "username": u["username"], "rol": u["rol"], "activo": u["activo"]}
        for u in usuarios_db
    ]

@app.post("/usuarios")
def crear_usuario(nuevo_usuario: Usuario, token: str = None):
    usuario = obtener_usuario_actual(token)
    validar_admin(usuario)
    if any(u["username"] == nuevo_usuario.username for u in usuarios_db):
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    usuario_obj = {
        "id": len(usuarios_db) + 1,
        "username": nuevo_usuario.username,
        "password": nuevo_usuario.password,
        "rol": nuevo_usuario.rol,
        "activo": True
    }
    usuarios_db.append(usuario_obj)
    return {
        "message": "Usuario creado",
        "data": UsuarioResponse(
            id=usuario_obj["id"],
            username=usuario_obj["username"],
            rol=usuario_obj["rol"],
            activo=usuario_obj["activo"]
        )
    }

# --- ENDPOINTS EXISTENTES (mejorados) ---
@app.get("/reactivos")
def obtener_reactivos(token: str = None):
    obtener_usuario_actual(token)
    return reactivos

@app.post("/reactivos")
def crear_reactivo(reactivo: Reactivo, token: str = None):
    obtener_usuario_actual(token)
    nuevo = {
        "id": len(reactivos) + 1,
        "nombre": reactivo.nombre,
        "stock": reactivo.stock,
        "vencimiento": reactivo.vencimiento,
        "unidadMedida": reactivo.unidadMedida,
        "proveedor": reactivo.proveedor
    }
    reactivos.append(nuevo)
    return {"message": "Reactivo creado", "data": nuevo}

@app.get("/equipos")
def obtener_equipos(token: str = None):
    obtener_usuario_actual(token)
    return equipos

@app.post("/equipos")
def crear_equipo(equipo: Equipo, token: str = None):
    obtener_usuario_actual(token)
    nuevo = {
        "id": len(equipos) + 1,
        "nombre": equipo.nombre,
        "estado": equipo.estado
    }
    equipos.append(nuevo)
    return {"message": "Equipo creado", "data": nuevo}

@app.get("/nanomateriales")
def obtener_nanomat(token: str = None):
    obtener_usuario_actual(token)
    return nanomateriales

@app.post("/nanomateriales")
def crear_nanomat(nano: Nanomaterial, token: str = None):
    obtener_usuario_actual(token)
    nuevo = {
        "id": len(nanomateriales) + 1,
        "nombre": nano.nombre,
        "descripcion": nano.descripcion
    }
    nanomateriales.append(nuevo)
    return {"message": "Nanomaterial creado", "data": nuevo}

@app.get("/ordenes")
def obtener_ordenes(token: str = None):
    obtener_usuario_actual(token)
    return ordenes

@app.post("/ordenes")
def crear_orden(orden: Orden, token: str = None):
    usuario = obtener_usuario_actual(token)
    for r in orden.reactivos:
        encontrado = None
        for item in reactivos:
            if item["nombre"] == r:
                encontrado = item
                break
        if not encontrado:
            raise HTTPException(status_code=400, detail=f"Reactivo {r} no existe")
        if encontrado["stock"] <= 0:
            raise HTTPException(status_code=400, detail=f"Sin stock: {r}")
        encontrado["stock"] -= 1
    nueva = {
        "id": len(ordenes) + 1,
        "nanomaterial": orden.nanomaterial,
        "reactivos": orden.reactivos,
        "equipo": orden.equipo,
        "usuarioResponsable": usuario["username"],
        "estado": "BORRADOR",
        "fechaCreacion": str(datetime.now().date()),
        "observaciones": orden.observaciones
    }
    ordenes.append(nueva)
    return {"message": "Orden creada", "data": nueva}

@app.put("/ordenes/{id}/estado")
def cambiar_estado(id: int, estado: str, token: str = None):
    usuario = obtener_usuario_actual(token)
    validar_admin(usuario)
    for o in ordenes:
        if o["id"] == id:
            o["estado"] = estado
            return {"message": "Estado actualizado", "data": o}
    raise HTTPException(status_code=404, detail="Orden no encontrada")
    return {"message": "Orden creada", "data": nueva}

# manejar estado de la orden
@app.put("/ordenes/{id}/estado")
def cambiar_estado(id: int, estado: str):

    for o in ordenes:
        if o["id"] == id:
            o["estado"] = estado

            if estado in ["Aprobada", "En proceso"]:
                actualizar_estado_equipo(o["equipo"], "Ocupado")

            elif estado in ["Completada", "Cancelada"]:
                actualizar_estado_equipo(o["equipo"], "Disponible")

            return {"message": "Estado actualizado", "data": o}

    return {"message": "Orden no encontrada"}