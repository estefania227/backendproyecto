from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #todas porque a veces sacaba error con localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# entidades con atributos
class Reactivo(BaseModel):
    nombre: str
    stock: int
    vencimiento: str


class Orden(BaseModel):
    nanomaterial:str
    reactivos: List[str]
    equipo: str


class Equipo(BaseModel):
    nombre: str
    estado: str


class Nanomaterial(BaseModel):
    nombre: str
    descripcion: str


# quemados prueba
reactivos = [{
        "id": 1,
        "nombre": "Ácido clorhídrico",
        "stock": 20,
        "vencimiento": "2026-12-31"
    }]

equipos = [{
        "id": 1,
        "nombre": "Microscopio",
        "estado": "Disponible"
    }]

nanomateriales = [
    {
        "id": 1,
        "nombre": "Nanooro",
        "descripcion": "Nanopartículas de oro"
    }
]

ordenes = []

def actualizar_estado_equipo(nombre_equipo: str, estado: str):
    for e in equipos:
        if e["nombre"] == nombre_equipo:
            e["estado"] = estado
            break

@app.get("/")
def home():
    return {"message": "prueba"}



@app.get("/reactivos")
def obtener_reactivos():
    return reactivos

@app.post("/reactivos")
def crear_reactivo(reactivo: Reactivo):

    nuevo = {
        "id": len(reactivos) + 1,
        "nombre": reactivo.nombre,
        "stock": reactivo.stock,
        "vencimiento": reactivo.vencimiento}

    reactivos.append(nuevo)

    return {"message": "Reactivo creado", "data": nuevo}



@app.get("/equipos")
def obtener_equipos():
    return equipos

@app.post("/equipos")
def crear_equipo(equipo: Equipo):

    nuevo = {
        "id": len(equipos)+1,
        "nombre": equipo.nombre,
        "estado": equipo.estado }

    equipos.append(nuevo)

    return {"message": "Equipo registrado", "data": nuevo}


@app.get("/nanomateriales")
def obtener_nanomateriales():
    return nanomateriales

@app.post("/nanomateriales")
def crear_nanomaterial(nano: Nanomaterial):

    nuevo = {
        "id": len(nanomateriales) + 1,
        "nombre": nano.nombre,
        "descripcion": nano.descripcion}

    nanomateriales.append(nuevo)

    return {"message": "Nanomaterial registrado", "data": nuevo}



@app.get("/ordenes")
def obtener_ordenes():
    return ordenes

@app.post("/ordenes")
def crear_orden(orden: Orden):

    # primero validar existencia de reactivos y descontar si se usa
    for r in orden.reactivos:
        encontrado = None

        for item in reactivos:
            if item["nombre"] == r:
                encontrado = item
                break

        if not encontrado:
            return {"message": f"Reactivo {r} no existe"}

        if encontrado["stock"] <= 0:
            return {"message": f"Sin stock: {r}"}

        encontrado["stock"]-=1

    
    nueva = {
        "id": len(ordenes) + 1,
        "nanomaterial": orden.nanomaterial,
        "reactivos": orden.reactivos,
        "equipo": orden.equipo,
        "estado": "Borrador"
    }

    ordenes.append(nueva)

    return {
        "message": "Orden registrada",
        "data": nueva }

# manejar estado de la orden
@app.put("/ordenes/{id}/estado")
def cambiar_estado(id: int, estado: str):

    for o in ordenes:
        if o["id"] == id:
            o["estado"] = estado

            # estado de los equipos por la orden
            if estado in ["Aprobada", "En proceso"]:
                actualizar_estado_equipo(o["equipo"], "Ocupado")
            elif estado in ["Completada", "Cancelada"]:
                actualizar_estado_equipo(o["equipo"], "Disponible")
            return {"message": "Actualizado", "data": o}

    return {"message": "Orden no encontrada"}