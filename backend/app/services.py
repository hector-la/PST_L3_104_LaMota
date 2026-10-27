from . import store
from .schemas import LecturaEntrada, ComandoLED

def guardar_lectura(datos: LecturaEntrada) -> dict:
    lectura = datos.model_dump()
    store.lecturas.append(lectura)
    # Conservamos como máximo las últimas 100 lecturas recibidas.
    del store.lecturas[:-100]
    return {"lectura": lectura, "led": store.estado_led["color"]}

def listar_lecturas() -> list[dict]:
    return store.lecturas

def consultar_led() -> dict:
    return store.estado_led

def cambiar_led(comando: ComandoLED) -> dict:
    store.estado_led["color"] = comando.color
    return store.estado_led

def promediar(n: int) -> dict:
    ultimas = store.lecturas[-n:]
    cantidad = len(ultimas)
    if cantidad == 0:
        return None
    temperaturas = [l["temperatura"] for l in ultimas]
    humedades = [l["humedad"] for l in ultimas]
    return {
        "cantidad": cantidad,
        "temperatura_promedio": round(sum(temperaturas) / cantidad, 2),
        "humedad_promedio": round(sum(humedades) / cantidad, 2),
    }

       
