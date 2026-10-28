# Laboratorio 3: Estructura de un backend

**Nombre:** Héctor Javier La Mota Camacho
**Paralelo:** 104 · **Docente:** Karen Torres · **Fecha:** 20-10-2026

## Objetivo
Entender cómo se organiza un backend leyendo, ejecutando y modificando una API de FastAPI. La API recibe temperatura y humedad de un ESP8266, las valida, las guarda en memoria y devuelve el color que debe mostrar un LED RGB.

## Cómo ejecutar
### Backend
Desde la carpeta `backend`, en Command Prompt:
```
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Swagger: http://127.0.0.1:8000/docs

### Firmware
1. Abrir la carpeta `firmware` con PlatformIO IDE en VS Code.
2. Copiar `include/config.example.h` como `include/config.h`.
3. En `config.h` completar la red WiFi de 2,4 GHz, `DISPOSITIVO` y `API_URL` con la IPv4 de la computadora (`ipconfig`), por ejemplo `http://<IPv4>:8000/lecturas`. No se usa localhost.
4. Con la placa conectada por USB, ejecutar Build, Upload y Monitor (115200 baudios).
5. `config.h` está en `.gitignore` y no se sube al repositorio.

## Pruebas de la Parte 3 (8 pruebas)
| # | Método | Ruta | Código esperado | Código obtenido |
|---|--------|------|-----------------|-----------------|
| 1 | GET | /salud | 200 | 200 |
| 2 | GET | /lecturas | 200 | 200 (lista vacía) |
| 3 | GET | /led | 200 | 200 (apagado) |
| 4 | PUT | /led | 200 | 200 (verde) |
| 5 | POST | /lecturas | 201 | 201 (led: verde) |
| 6 | GET | /lecturas | 200 | 200 (4 lecturas) |
| 7 | POST | /lecturas (humedad 150) | 422 | 422 (less_than_equal) |
| 8 | PUT | /led (color amarillo) | 422 | 422 (literal_error) |

Nota: en el POST usé los valores por defecto de Swagger (dispositivo "string", temperatura 50, humedad 100).

## Cambio guiado (Parte 5)
- Archivo modificado: `backend/app/routes.py`
- Qué cambió en la respuesta: `GET /salud` ahora devuelve `{"estado": "ok", "laboratorio": 3}` (31 bytes en lugar de 15).

## Respuestas a las preguntas
1. **¿Qué función recibe el JSON y cuál lo guarda?** Lo recibe `post_lectura` en `routes.py` (parámetro `datos: LecturaEntrada`). Lo guarda `guardar_lectura` en `services.py`, que lo agrega a `store.lecturas` y conserva las últimas 100.
2. **¿Qué archivo cambiarías para añadir una URL?** `routes.py`. Solo tocaría `services.py` si la ruta necesita lógica nueva y `schemas.py` si recibe un JSON con campos nuevos.
3. **¿Qué pasa con las lecturas y el color al reiniciar la API?** Se borran y el LED vuelve a "apagado", porque ambos viven solo en la memoria del proceso (`store.py`).
4. **¿Por qué un JSON bien escrito puede devolver 422?** Porque FastAPI valida los datos con los modelos de `schemas.py` antes de ejecutar la función de la ruta. Humedad 150 supera `le=100` y "amarillo" no está en el `Literal` de `ComandoLED`. No se ejecuta `services.py` y no se guarda nada.
5. **Recorrido de una lectura:** el ESP8266 hace `POST /lecturas` cada 5 s → `routes.py` (`post_lectura`) → `schemas.py` valida con `LecturaEntrada` (si falla, 422) → `services.guardar_lectura` la agrega a `store.lecturas` → responde 201 con `{"lectura": ..., "led": color}`. El LED cambia cuando el firmware recibe ese 201 y ejecuta `aplicarColor`. Un `PUT /led` solo cambia el estado del servidor; el LED lo refleja en el siguiente envío (hasta 5 s).

## Reto: GET /lecturas/promedio
Prueba controlada (API reiniciada, ESP8266 desconectado):

| Consulta | Código esperado | Código obtenido | Resultado obtenido |
|----------|-----------------|-----------------|--------------------|
| Antes de enviar datos | 404 | 404 | `{"detail": "No hay lecturas"}` |
| ?n=3 | 200 | 200 | cantidad 3, temperatura_promedio 24, humedad_promedio 50 |
| ?n=2 | 200 | 200 | cantidad 2, temperatura_promedio 26, humedad_promedio 55 |
| ?n=5 | 200 | 200 | cantidad 3, temperatura_promedio 24, humedad_promedio 50 |
| ?n=0 | 422 | 422 | `greater_than_equal` (n debe ser mayor o igual a 1) |
| ?n=101 | 422 | 422 | `less_than_equal` (n debe ser menor o igual a 100) |
| Sin indicar n | 200 | 200 | cantidad 3, temperatura_promedio 24, humedad_promedio 50 (igual que n=3) |

Se enviaron tres lecturas de `equipo01` (20/40, 24/50 y 28/60) y al terminar `GET /lecturas` seguía mostrando las tres, así que el cálculo no modifica `store.lecturas`. Nota: Swagger UI bloquea `n=0` y `n=101` en el navegador antes de enviar la petición, por eso los 422 se comprobaron con la URL directa.

Explicación de cómo lo resolví: en `routes.py` añadí `GET /lecturas/promedio` con `n: int = Query(default=3, ge=1, le=100)`, así FastAPI usa 3 si no se indica `n` y responde 422 fuera de 1 a 100. La ruta llama a `services.promediar(n)` y, si devuelve `None` (no hay lecturas), lanza `HTTPException` 404 con un mensaje explicativo. En `services.py`, `promediar` toma las últimas `n` lecturas con `store.lecturas[-n:]` (una copia, no modifica la lista), cuenta con `len` cuántas se usaron y calcula cada promedio con `sum` dividido entre esa cantidad, con `round(..., 2)`. Divido entre la cantidad real y no entre `n` para que con menos de `n` lecturas el promedio siga siendo correcto (con `n=5` y 3 lecturas devuelve `cantidad` 3).

## Hardware real (Parte 4)
- Montaje con NodeMCU ESP8266, **DHT22 (AM2302)** en D1 y LED RGB de cátodo común en D5, D6 y D7.
- El monitor serie (115200 baudios) mostró `HTTP 201` con el dispositivo `equipo01` y el campo `led` de la respuesta.
- Estados del LED registrados en el monitor: rojo, azul y apagado. El verde se probó en Swagger (PUT y POST) y se ve encendido en la fotografía, pero no quedó capturado en el monitor.
- El LED RGB llegó a encenderse en verde (fotografía del montaje en el informe). Los estados rojo, azul y apagado los registré con el campo `led` de la respuesta de la API.
- Las lecturas del sensor no son confiables (temperatura de 1.0 a 2.5 °C y humedad cercana a 24 %): el firmware declara `DHT11` y el sensor es un DHT22. Lo más probable es que baste declarar `DHT22` en `main.cpp`.

## Notas
No se publican config.h, contraseñas ni tokens.
