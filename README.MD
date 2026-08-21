# Proyecto Emergency Control

Guía de instalación, ejecución, prueba e interpretación del agente autónomo.

---

## 1. Instalar dependencias

El proyecto requiere:

- **Python 3.14**
- **Node.js y npm**

### Backend

Desde la carpeta raíz del proyecto:

```powershell
cd project/backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

En una terminal nueva:

```powershell
cd project/frontend
npm install
```

---

## 2. Iniciar el backend

Desde `project/backend`, con el entorno virtual activado:

```powershell
uvicorn main:app --app-dir src --port 8000
```

El backend quedará disponible en:

```
http://127.0.0.1:8000
```

Para comprobar que está funcionando, abrir:

```
http://127.0.0.1:8000/api/health
```

>  No cierre esta terminal mientras se esté utilizando el frontend.

---

## 3. Iniciar el frontend

En una segunda terminal:

```powershell
cd project/frontend
npm run dev
```

Vite iniciará la aplicación en:

```
http://localhost:5173/
```

Abrir esa dirección en el navegador.

---

## 4. Ejecutar el agente

El agente se ejecuta mediante el endpoint:

```
POST /api/solve
```

El frontend realiza esta solicitud automáticamente al ejecutar la misión.

**Para ejecutar el agente:**

1. Mantener el backend ejecutándose en `http://127.0.0.1:8000`
2. Mantener el frontend ejecutándose en `http://localhost:5173/`
3. Abrir la aplicación en el navegador
4. Ejecutar la misión desde la interfaz

El backend recibe el escenario, ejecuta el planificador y devuelve el plan de acciones para que el frontend lo reproduzca.

---

## 5. Probar una misión

Con el backend y el frontend ejecutándose:

1. Abrir: `http://localhost:5173/`
2. Ejecutar la misión desde la interfaz
3. El frontend solicitará el plan al backend mediante `POST /api/solve`
4. La interfaz mostrará la ejecución del plan paso a paso

### Durante la ejecución se pueden observar:

- Posición del robot
- Batería disponible
- Acciones realizadas
- Objetos transportados
- Costo acumulado
- Progreso de la misión
- Estado final de las estaciones

### Resultado de prueba

Con el escenario utilizado durante la validación, el agente produjo una solución válida:

```
MISSION COMPLETE — all stations ONLINE
Plan total: 88
Steps: 33
```

La ejecución finalizó con las tres estaciones objetivo en estado **ONLINE**:

- `GENERATOR`
- `COMMAND`
- `ARTILLERY`

El plan incluyó operaciones de movimiento, recogida de objetos, apertura de puertas, reparación, activación y recarga.

---

## 6. Interpretar el resultado

### Misión completada

Si la ejecución termina mostrando:

```
MISSION COMPLETE — all stations ONLINE
```

significa que el plan alcanzó la condición objetivo de la misión.

El valor:

```
Plan total: 88
```

representa el costo acumulado de todas las acciones ejecutadas.

Por ejemplo:

```
[001] PICKUP KEY1 (cost 1)
[002] INTERACT OPEN_DOOR DOOR1 (cost 2)
[003] MOVE Z1→Z2 (cost 4)
```

Cada acción tiene un costo y el costo total corresponde a la suma de los costos de las acciones del plan.

### Batería

La batería se actualiza durante la ejecución. Por ejemplo:

```
[010] MOVE Z2→Z3 (cost 6, bat 35)
```

indica que después de esa acción el robot dispone de 35 unidades de batería.

Cuando se ejecuta una recarga:

```
[019] INTERACT RECHARGE CHARGER_1 (cost 3, bat 100)
```

la batería vuelve a su capacidad máxima.

### Fallo de la misión

- Si el agente no encuentra un plan válido, debe indicar que **no existe solución (FAILURE)**.
- Si durante la ejecución un paso viola una regla del escenario, la simulación debe **detenerse** e indicar el problema correspondiente.

---

## Ejecución completa

### Terminal 1 — Backend

```powershell
cd project/backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --app-dir src --port 8000
```

### Terminal 2 — Frontend

```powershell
cd project/frontend
npm install
npm run dev
```

Después abrir:

```
http://localhost:5173/
```

y ejecutar la misión.

El resultado esperado es un plan ejecutado por el agente que permita alcanzar:

```
GENERATOR = ONLINE
COMMAND = ONLINE
ARTILLERY = ONLINE
```

junto con el costo total y el registro de las acciones ejecutadas.