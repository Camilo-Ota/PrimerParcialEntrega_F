# Diseño del agente

Este documento debe completarse **antes** de la implementación principal del agente.

Use sus propias palabras y notación. No reemplace este archivo por una transcripción
del enunciado. Las subsecciones existen para que no se le olvide una decisión;
usted decide el contenido.

El entorno, según las propiedades vistas en clase, es totalmente observable,
determinista, secuencial, estático, discreto y de agente único. Bajo esas
condiciones la solución es un **plan completo** y el marco correcto es la
búsqueda clásica. Justifique cada componente con ese marco (AIMA, cap. 3).

---

## Estado

### Definición formal

*Escriba la tupla de estado. Cada componente debe ser una variable que el robot necesita para saber qué podrá hacer después.*

El estado del agente se representa como una tupla con cinco componentes, cada uno correspondiente a una variable que cambia a medida que se ejecutan las acciones:

**s = ⟨ ubicación del robot, nivel de batería, inventario del robot, distribución de objetos en el escenario, estado lógico del entorno ⟩**

A continuación se describe cada componente:

1. **Ubicación actual del robot.** Es la zona discreta de la instalación en la que se encuentra físicamente el robot (por ejemplo, Zona A, Zona B o Pasillo Central). El agente necesita saber dónde está para determinar qué corredores adyacentes tiene disponibles para moverse y con qué elementos o sistemas de la instalación puede interactuar directamente.

2. **Nivel de energía de la batería.** Es un valor numérico entero que registra la carga actual disponible en la batería del robot. Es un limitante físico directo: el robot solo puede trasladarse a otra zona si su batería actual es mayor o igual al costo de energía del corredor. Además, rastrear este nivel es lo que permite al algoritmo de búsqueda aplicar reglas de dominancia en la lista de estados explorados (si llegamos al mismo lugar con menos batería y a un costo mayor, ese camino se descarta).

3. **Inventario (carga del robot).** Son las herramientas reutilizables y los materiales consumibles que el robot lleva cargados encima en ese momento. Controla dos reglas físicas:
   - *Capacidad de transporte:* impide que el robot recoja más peso o volumen del permitido por su diseño.
   - *Precondición de operaciones:* determina si el robot puede ejecutar una tarea de mantenimiento específica (por ejemplo, no puede reemplazar una placa si no lleva un repuesto en su inventario).

   Los objetos idénticos no se diferencian con identificadores individuales (no hay "Fusible 1" o "Fusible 2"); el estado solo almacena la cantidad física en posesión (por ejemplo, dos fusibles). Esto evita que el espacio de búsqueda se multiplique innecesariamente.

4. **Distribución de objetos en el escenario.** Es la ubicación física y las cantidades de todas las herramientas y materiales que están repartidos por el suelo de las distintas zonas de la instalación. Permite saber si la acción de recoger algo es legal en la zona actual (el objeto debe estar allí) y permite actualizar el mundo cuando el agente decide dejar un objeto en el suelo.

5. **Estado físico y lógico del entorno.** Es un conjunto de variables lógicas (verdadero/falso) que definen el estado operativo de los sistemas de la instalación (por ejemplo, si una puerta está abierta o si un reactor está desconectado). Las operaciones de mantenimiento modifican permanentemente estas variables; muchas acciones dependen de que otras se hayan realizado previamente (por ejemplo, el reactor debe estar desconectado antes de iniciar una reparación); y la prueba de meta se evalúa directamente sobre este componente: la misión tiene éxito únicamente cuando los sistemas lógicos críticos están en su configuración segura.

### Por qué cada variable es necesaria

*Criterio de clase (Applicable): una variable pertenece al estado si y solo si dos configuraciones que difieran en ella pueden diferir en las acciones legales futuras o en su resultado.*

*Pase ese filtro con cada variable. En particular: la batería forma parte de la situación física; la posición de los objetos no se deduce del escenario inicial si el robot puede soltarlos (DROP); los cambios permanentes (puertas, paneles, estaciones) condicionan el futuro.*

1. **Ubicación actual del robot.** Si tenemos dos configuraciones idénticas en todo, excepto en que en la primera el robot está en la Zona A y en la segunda está en la Zona B, el conjunto de acciones legales futuras cambia drásticamente: desde la Zona A, la acción de moverse solo será legal hacia las zonas directamente conectadas a la Zona A. Además, las acciones de mantenimiento o de recoger materiales solo son aplicables sobre los objetos y sistemas que físicamente coexistan en la zona donde se encuentra detenido el robot en ese instante. Por lo tanto, es una variable de estado obligatoria.

2. **Nivel de energía de la batería.** Dos situaciones idénticas en el mapa pero con distinto nivel de energía representan estados físicos diferentes, porque condicionan la legalidad del movimiento futuro. Si el robot necesita cruzar un corredor que consume 15 unidades de energía, moverse será legal con una batería de 20, pero será ilegal (o conducirá a una falla) con una batería de 10. Además, la batería es indispensable para evaluar la dominancia en la lista de estados explorados: si un camino llega al mismo entorno físico pero con menor batería y a un costo mayor o igual, se descarta porque no puede mejorar el plan futuro.

3. **Posición de los objetos en el escenario.** Si dos mundos son idénticos pero en uno un material consumible está en la Zona C y en el otro está en la Zona D, las acciones del robot se ven directamente afectadas. Como el robot tiene permitido soltar elementos temporalmente en cualquier zona, la ubicación de las herramientas y consumibles no se puede deducir de forma fija a partir del escenario inicial. El robot solo puede recoger un objeto si dicho objeto se encuentra en el suelo de su zona actual; si el objeto cambió de ubicación debido a una acción previa de dejarlo, la legalidad de recogerlo en las distintas zonas del mapa se altera por completo.

4. **Inventario / carga del robot.** Dos configuraciones que difieran únicamente en lo que el robot lleva en su inventario cambian por completo las acciones permitidas a continuación. El inventario condiciona el futuro en dos sentidos: por límite físico, si el robot lleva herramientas que igualan su capacidad máxima de transporte, ya no puede recoger otro objeto pesado; y por requisito de operaciones, las tareas de mantenimiento requieren que el robot tenga en su inventario las herramientas reutilizables y los materiales consumibles necesarios (por ejemplo, reemplazar una pieza solo es legal si el robot lleva el repuesto encima).

5. **Estado físico y lógico del entorno.** Los cambios permanentes en los sistemas e infraestructura de la instalación modifican la física del problema para todos los pasos subsecuentes. Las operaciones ejecutadas por el robot modifican permanentemente el entorno (activar un sistema, desbloquear una puerta o habilitar una estación de carga). Si una puerta entre la Zona A y la Zona B está bloqueada, moverse entre ellas es ilegal; una vez que el robot ejecuta la acción de desbloqueo, ese cambio hace que el movimiento pase a ser legal. Igualmente, las dependencias operativas (como requerir que un sistema esté apagado antes de reemplazar una pieza) hacen que el estado de los interruptores determine la aplicabilidad de las acciones de reparación posteriores.

### Qué información se deriva y NO se almacena

*Peso de la carga, grafo de corredores, costos, capacidad, batería máxima, etc. Si se puede calcular a partir del estado y de las constantes del escenario, no es una variable de estado.*

Para mantener el espacio de estados lo más compacto y eficiente posible, se distingue entre variables de estado que cambian en el tiempo y aspectos permanentes del entorno (constantes). Si un dato puede calcularse o deducirse en tiempo de ejecución combinando el estado actual con la configuración estática del escenario, no debe formar parte del estado de búsqueda.

**Constantes físicas y del escenario (no cambian durante la misión):**
- El grafo de corredores y su conectividad: qué zonas están conectadas entre sí y a través de qué corredores es fijo y conocido de antemano; se consulta en el mapa, no en el estado dinámico.
- Los costos de los corredores: la cantidad de energía consumida por cruzar cada corredor es una propiedad estática del escenario.
- Las capacidades límite del robot: tanto la batería máxima como la capacidad física máxima de transporte son valores fijos definidos por el problema.
- Las propiedades y pesos de los objetos: el peso individual de cada herramienta o material y su naturaleza (herramienta reutilizable o material consumible) son constantes que no cambian a lo largo de la misión.
- Las reglas de dependencias y operaciones: qué herramientas y consumibles se requieren simultáneamente para una tarea son reglas fijas del mundo, no variables.

**Datos derivados (se calculan al vuelo, no se guardan):**
- El peso actual de la carga: se calcula sumando las cantidades de objetos en el inventario multiplicadas por sus pesos individuales constantes.
- La capacidad de carga disponible: es una simple resta entre la capacidad máxima y el peso actual.
- El costo acumulado del plan: no pertenece al estado físico del robot. Se guarda y se actualiza únicamente como un dato del Nodo de búsqueda, acumulando la suma de los costos de las acciones recorridas.
- La legalidad o aplicabilidad de las acciones: la posibilidad de moverse a una zona vecina o realizar una operación de mantenimiento no se almacena como un atributo; se evalúa al vuelo comprobando si el estado actual cumple las restricciones del escenario (por ejemplo, si la batería alcanza para el corredor).

Excluir esta información redundante o constante permite una abstracción más eficiente: protege al algoritmo de búsqueda de multiplicar innecesariamente estados idénticos en la lista de explorados, y deja que la frontera de búsqueda se concentre únicamente en las decisiones que realmente cambian el curso de la misión.

### Qué pertenece al historial de búsqueda y no al estado físico

*g(n), el padre y la acción que trajo aquí describen cómo llegó, no dónde está. Viven en el Nodo. Si se meten en el estado, la lista de explorados no puede reconocer la misma situación física alcanzada por dos rutas.*

Es fundamental trazar una línea divisoria estricta entre dos estructuras de datos distintas:

- **El Estado:** es una representación estática de la situación física y lógica del mundo en un momento determinado. Responde únicamente a la pregunta «¿en qué situación física se encuentra el entorno y el robot ahora mismo?» (la zona en la que está el robot, su batería, su inventario, la distribución de objetos y el estado lógico del entorno).
- **El Nodo de búsqueda:** es una estructura auxiliar que crea el algoritmo para construir el árbol de exploración. Representa un plan parcial en construcción; es el "envoltorio" del estado y encapsula la historia del camino recorrido para llegar a él.

La siguiente información de control pertenece única y exclusivamente al Nodo, y nunca debe formar parte del Estado:

- **El costo acumulado del camino:** representa la suma de la energía consumida por todas las acciones ejecutadas desde el estado inicial hasta el nodo actual. Es un dato numérico que la frontera de búsqueda usa para decidir qué nodo expandir primero.
- **El puntero al nodo padre:** es la referencia al nodo anterior en el árbol de exploración. Su único propósito es permitir que, una vez alcanzada la meta, el agente pueda reconstruir la secuencia final de acciones ascendiendo por la cadena de padres.
- **La acción que trajo aquí:** el operador (movimiento o mantenimiento) aplicado en el nodo padre para generar la situación actual.
- **La profundidad:** el número de pasos realizados desde el nodo raíz hasta el nivel actual del árbol.

**¿Por qué es un problema mezclar estos conceptos?**

El algoritmo de búsqueda en grafos necesita comprobar de manera sistemática si un estado físico ya fue visitado y expandido con anterioridad. Esto se hace consultando la lista de explorados, que guarda las "firmas" de los estados ya procesados para evitar bucles infinitos o ciclos redundantes.

Si se comete el error de guardar variables de control (como el costo acumulado o la referencia al nodo padre) dentro del Estado:
- La lista de explorados deja de funcionar: si el robot llega a la misma configuración del mundo mediante dos rutas distintas —una ineficiente y otra óptima— el algoritmo las evaluará como estados "diferentes" porque sus costos acumulados difieren.
- Se produce una explosión combinatoria: al considerarlos estados distintos, el algoritmo expandirá ambas ramas de manera independiente, duplicando nodos en memoria y provocando que un espacio de estados pequeño se vuelva inmanejable.
- Se vuelve inviable comparar caminos: algoritmos como la búsqueda de costo uniforme necesitan comparar el costo acumulado al llegar a un mismo estado para descartar el camino peor. Si el costo acumulado está metido en el propio estado, el algoritmo nunca podrá hacer esa comparación.

En conclusión, el Estado almacena la física del problema (el dónde y el qué), mientras que el Nodo almacena la historia de la computación (el cómo). Separar estos conceptos permite que la comparación de igualdad entre estados sea eficiente, garantizando que la lista de explorados detecte repetidos de forma instantánea.

### Cuándo dos configuraciones son el mismo estado

*Materiales equivalentes por tipo: no les ponga ids artificiales. Estructuras canónicas (conjuntos, contadores) para que la comparación de igualdad y el hash coincidan con la equivalencia física. Sin eso, la búsqueda en grafos explota.*

La eficiencia de la lista de explorados depende críticamente de que el algoritmo reconozca de forma instantánea si una situación ya fue visitada. Si dos configuraciones del mundo representan exactamente la misma realidad física pero se programan con estructuras internas distintas, la comparación de igualdad fallará y el algoritmo explorará caminos repetidos indefinidamente hasta agotar la memoria.

**Agregación en lugar de identificadores individuales.** Los materiales equivalentes por tipo no deben tener identificadores artificiales (evitar modelar "tornillo 1" y "tornillo 2" o "placa A" y "placa B"). Distinguirlos de forma artificial genera permutaciones inútiles en el espacio de búsqueda: llevar la placa A es físicamente idéntico a llevar la placa B, pero computacionalmente se tratarían como estados distintos, multiplicando innecesariamente las posibilidades. La representación correcta es usar cantidades puras por tipo de objeto (por ejemplo, "2 placas de repuesto").

**Estructuras de datos canónicas.** Las colecciones que representan el inventario o la distribución de objetos en las zonas deben tener un formato canónico e inmutable.
- Usar listas para representar qué objetos hay en una zona es un error: una lista con los objetos en un orden es distinta, computacionalmente, de la misma lista en otro orden, aunque representen exactamente la misma situación física.
- La solución es usar estructuras donde el orden no importe: conjuntos inmutables para objetos únicos (herramientas que simplemente se poseen o no), y colecciones ordenadas de pares "tipo de objeto–cantidad" para materiales acumulativos. Esto asegura que la comparación de igualdad de dos estados coincida con total precisión con la igualdad física del entorno.

**Transposiciones.** En la planificación es muy común el fenómeno de la transposición: alcanzar la misma configuración del mundo a través de distintas secuencias de acciones. Si el robot recoge primero un fusible y luego una batería, o al revés, la situación resultante es la misma. Usar estructuras canónicas es la única forma de garantizar que la búsqueda en grafos detecte estas transposiciones de manera instantánea, evitando que el algoritmo explore caminos equivalentes por separado.

### Relevancia: objetos que ya no cambian el futuro

Los cambios del entorno son **monótonos** (una puerta abierta no se cierra).
Pregúntese: una llave cuya puerta ya está abierta, o una herramienta cuyo panel
ya está reparado, ¿sigue distinguiendo estados si solo cambia *dónde* está en
el suelo? Si no habilita ninguna acción futura, incluirla multiplica el espacio
con permutaciones de objetos muertos. Justifique si las ignora y por qué eso
no pierde el óptimo.

Ignorar la ubicación física de los objetos que ya cumplieron su propósito es una decisión de diseño válida, óptima y necesaria. A continuación se justifica:

**1. Aplicando el criterio de relevancia.** Una variable pertenece al estado si y solo si dos configuraciones que difieran únicamente en ella pueden diferir en las acciones legales futuras. Consideremos el caso de una llave cuya puerta asociada ya fue abierta de forma permanente:
- Configuración A: el robot lleva la llave en su inventario, la puerta está abierta.
- Configuración B: la llave está en el suelo de otra zona, la puerta está abierta.

¿Difieren estas dos configuraciones en sus acciones futuras o consecuencias? No. Como la puerta está abierta de forma irreversible, ninguna acción futura vuelve a requerir la llave como condición. Por lo tanto, la ubicación de la llave deja de tener impacto sobre la legalidad de cualquier acción posterior, y su posición debe eliminarse del estado.

**2. Evitando la explosión por permutación.** Si el agente no ignora la posición de estos "objetos muertos", el espacio de estados sufre una explosión combinatoria: el algoritmo expandirá nodos físicamente idénticos solo porque una llave inútil quedó tirada en una zona u otra. Al ignorar esa variable (o mapearla a un único valor, como "descartada"), se agrupan múltiples estados del mundo en una sola clase de equivalencia, y la lista de explorados puede reconocerlos como el mismo estado físico, deteniendo el crecimiento innecesario de la frontera de búsqueda.

**3. Preservando la optimalidad.** Esta poda no hace perder la solución óptima por dos razones:
- El subproblema restante para alcanzar la meta es exactamente el mismo, sin importar dónde quedó el objeto muerto; las transiciones activas del robot conservan las mismas condiciones y efectos.
- El costo acumulado del plan solo se consume por acciones físicas que cambian el entorno o trasladan al robot; como el agente no necesita hacer ninguna acción adicional sobre los objetos muertos para llegar a la meta, el camino de menor costo del escenario reducido sigue siendo el mismo que el del escenario original.

**En conclusión:** El agente puede abstraer la ubicación en el suelo de un objeto cuando ese
objeto ya no puede habilitar ninguna acción futura relevante. Esta abstracción
se aplica a la ubicación del objeto en el suelo, no necesariamente a su
presencia en el inventario.

Si un objeto muerto permanece en el inventario, sigue formando parte de la
situación física porque conserva su peso y, por tanto, puede afectar la
capacidad disponible para recoger otros objetos. Por eso, el agente no elimina
automáticamente un objeto muerto del inventario: únicamente deja de distinguir
su ubicación en el suelo cuando esa ubicación ya no puede afectar acciones
futuras.

En consecuencia, la representación distingue entre:

- objeto muerto en el suelo: su ubicación puede abstraerse si ya no tiene
  ninguna utilidad futura;
- objeto muerto en el inventario: su peso sigue siendo relevante hasta que el
  robot decida realizar un DROP legal y útil.

Esta distinción permite reducir estados equivalentes sin violar las
restricciones físicas de capacidad.

---

## Acciones

Defina las acciones **internas** del agente (nombres libres). Para cada una:
precondiciones, efectos, costo. Toda acción del mundo exige además
**batería ≥ costo**.

### Tabla de acciones internas

| Acción | Precondiciones | Efectos | Costo |
|---|---|---|---|
| **MOVER(Origen, Destino)** | El robot está en Origen. Existe un corredor directo entre Origen y Destino. Si el corredor tiene una puerta, esta debe estar desbloqueada. La batería alcanza para cubrir el consumo del corredor. | La posición del robot cambia a Destino. La batería disminuye según el costo del corredor. | El costo de energía del corredor recorrido. |
| **RECARGAR()** | El robot está en una zona con estación de recarga. La batería actual es menor a la máxima. | La batería del robot se restaura por completo. | Un costo mínimo positivo (para evitar bucles). |
| **PICKUP(Objeto)** | El objeto está físicamente en el suelo de la zona actual. El peso del objeto no excede la capacidad de carga restante del robot. El objeto no es un "objeto muerto" y es necesario para una meta futura pendiente. | El inventario del robot aumenta en ese objeto. La cantidad del objeto en el suelo disminuye. | Costo unitario de manipulación. |
| **DROP(Objeto)** | El robot lleva el objeto en su inventario. Solo se genera si el robot necesita liberar peso para recoger un objeto crítico en la zona actual. | El inventario del robot disminuye en ese objeto. El objeto se añade al suelo de la zona. | Costo unitario de manipulación. |
| **OPERAR(Equipo, Operación)** | El robot está en la zona del equipo. Se cumplen las dependencias lógicas del entorno (por ejemplo, el sistema está desconectado). El robot posee en su inventario las herramientas y materiales necesarios. | Se descuentan del inventario los materiales consumibles utilizados. Las herramientas reutilizables se conservan. El estado lógico del equipo se actualiza de forma permanente. | Costo operativo específico de la tarea (no negativo). |

### Decisiones de formulación para evitar la explosión de estados

En línea con el principio de mínimo compromiso, la generación de sucesores de las acciones PICKUP y DROP se restringió con criterios lógicos racionales:

**1. Control de la generación de DROP.** El simulador permite físicamente soltar un objeto en cualquier zona. Sin embargo, si el agente generara la acción DROP en cada estado posible, el número de acciones posibles por estado crecería de forma exponencial, forzando al algoritmo de búsqueda a simular infinitas trayectorias donde el robot traslada materiales sin propósito. Un plan óptimo nunca ejecuta un DROP en un corredor vacío a menos que sea estrictamente necesario para liberar capacidad de carga para un objeto más prioritario. Por eso, el agente solo genera DROP si el estado actual exige liberar peso para poder realizar un PICKUP crítico. Esto elimina millones de ramas muertas sin perder jamás la solución de menor costo.

**2. Eliminación de acciones sobre "objetos muertos".** Una vez que una variable del entorno cambia permanentemente (por ejemplo, un reactor queda activo o una puerta queda abierta), las herramientas específicas que se requirieron para esa única tarea pierden toda utilidad. El robot no genera acciones de recoger herramientas cuyas tareas asociadas ya fueron completadas con éxito. Considerar estas acciones equivaldría a expandir permutaciones de "estados muertos" en la búsqueda, aumentando inútilmente el consumo de memoria.

**3. Agregación de objetos equivalentes.** No se definen acciones específicas sobre identificadores únicos (como recoger la "placa auxiliar A" o la "placa auxiliar B"). Las acciones se instancian sobre el tipo de objeto genérico, incrementando o disminuyendo los contadores del estado. Esto reduce el espacio de búsqueda al tratar las transiciones de forma puramente cuantitativa.

### `Applicable` interno vs legalidad del contrato

El simulador dice cuándo un paso es legal. Su generador de sucesores dice qué
acciones son relevantes para buscar. No tienen que ser el mismo conjunto.

El contrato permite DROP en cualquier zona si el objeto está en la carga. Si
su agente genera ese DROP en cada estado con carga, el espacio deja de ser
«5 zonas y unas tareas» y pasa a ser «en cuál de las 5 zonas quedó cada
objeto». Eso no se arregla cambiando la capacidad de carga ni apagando la batería:
el escenario es la fuente de verdad y el profesor probará otras instancias.

Usted puede (y se espera que) restrinja DROP —y cualquier otra acción— a los
casos que un plan óptimo podría necesitar. Justifique que ningún plan de costo
mínimo usa una acción que usted dejó de generar.

**Cuándo genera DROP el agente**

El generador de sucesores del agente genera la acción DROP únicamente cuando se cumplen a la vez estas condiciones:
1. **Saturación de carga:** el robot está en una zona donde hay un objeto en el suelo que es necesario para una tarea futura.
2. **Capacidad insuficiente:** el robot no tiene suficiente capacidad libre para recoger ese objeto.
3. **Liberación óptima:** el robot suelta un elemento que no se requiere de forma inmediata en los pasos siguientes, para liberar el peso exacto que le permita recoger el objeto prioritario.

En cualquier otro caso, la acción DROP no se genera, obligando al robot a llevar los objetos consigo de manera persistente.

**Por qué no se pierde el óptimo**

- Llevar objetos no consume energía extra: el costo de moverse depende solo del corredor, no de si el robot viaja cargado o vacío.
- Evitar costos de manipulación redundantes: soltar y volver a recoger un objeto que no estorbaba habría sumado dos costos de manipulación innecesarios; un plan óptimo siempre preferirá mantenerlo guardado durante el trayecto.
- Abandonar un objeto sin necesidad suma un costo innecesario al plan, y la meta no premia dejar objetos tirados.
- Las operaciones de mantenimiento se realizan directamente desde el inventario: el robot no necesita soltar las herramientas en el suelo para poder usarlas.

**Conclusión:** La generación de DROP se restringe a situaciones en las que existe una
necesidad real de liberar capacidad para recoger un objeto que puede ser
relevante para una tarea pendiente.

La razón de esta restricción es que transportar un objeto no aumenta el costo
de movimiento, mientras que PICKUP y DROP sí tienen costo positivo. Por tanto,
si un objeto puede permanecer en el inventario sin impedir ninguna acción
necesaria, moverlo al suelo y recogerlo posteriormente solo añade costo y no
mejora el estado del mundo.

Por ello, el generador no considera DROP como una acción de transporte o
reorganización arbitraria del inventario. Solo la genera cuando liberar
capacidad puede ser necesario para continuar con un plan válido y de costo
mínimo.

Esta es una restricción del conjunto de sucesores de la búsqueda, no una
modificación de las reglas físicas del simulador: el contrato sigue
permitiendo DROP cuando el objeto está en el payload.

## Modelo de transición

$$s \xrightarrow{a} s' \qquad \text{solo si } a \in Applicable(s)$$

Esta expresión dice que solo se puede pasar del estado $s$ al estado $s'$ mediante la acción $a$ si esa acción es una de las acciones legales en $s$ (si $s$ cumple las precondiciones de $a$). Esa acción legal transforma el estado actual $s$ en un nuevo estado $s'$: la función que hace esa transformación se puede llamar `Result(s, a)`.

Una acción solo puede aplicarse sobre un estado si ese estado cumple sus
precondiciones. El resultado de aplicar la acción es determinista y parcial:
solo se define para las acciones que sí son aplicables en el estado actual.
Bajo el marco de la búsqueda clásica, ejecutar una acción legal en un estado
dado produce siempre un único estado sucesor, de forma predecible.

**Qué puede cambiar tras una acción:**
- **Zona del robot:** cambia de forma discreta de una zona a otra únicamente mediante la acción de moverse, siempre que las zonas estén conectadas y los corredores o puertas no estén bloqueados.
- **Carga y suelo:** recoger y soltar objetos altera cuantitativamente la presencia de objetos en el escenario y en el inventario del robot. Además, reparar consume de forma irreversible los materiales consumibles del inventario, reduciendo también el peso de la carga.
- **Batería:** disminuye con el costo específico de cada acción física ejecutada (movimientos o interacciones). Se restaura por completo al aplicar con éxito la recarga en una zona con estación habilitada.
- **Entorno persistente:** el estado lógico de la instalación cambia de forma monótona (un cambio seguro no se revierte). Acciones como abrir una puerta, reparar o activar un sistema modifican permanentemente estas variables, desbloqueando accesos o habilitando sistemas necesarios para la meta.

**Qué se preserva:**
- Las constantes del escenario (la topología fija de las zonas, los pesos de cada tipo de material, las restricciones de carga del robot y los costos de las acciones) no se modifican y permanecen fuera del estado de búsqueda, como conocimiento fijo.
- Cada variable de estado que no se mencione explícitamente en los efectos de una acción permanece completamente inalterada en el estado siguiente. Por ejemplo, el nivel de batería no cambia por recoger un objeto si esa acción no tiene costo de energía asociado, ni el estado de reparación de un sistema cambia mientras el robot simplemente se desplaza entre corredores.

**Canonicalización del estado**

Para que la búsqueda en grafos funcione de manera óptima y no se sature de duplicados en memoria, el estado resultante se normaliza inmediatamente después de cada transición:
- Las colecciones que representan la carga en el inventario y los objetos en el suelo se ordenan siempre de la misma forma (por ejemplo, alfabéticamente por tipo de objeto) y se convierten en estructuras inmutables. Esto garantiza que dos estados físicamente iguales se reconozcan siempre como iguales.
- Si un panel fue reparado de forma permanente, o una puerta fue abierta de manera irreversible, el agente elimina activamente del estado las herramientas y llaves que ya cumplieron su propósito y no tienen uso futuro. Esto evita que el algoritmo explore permutaciones inútiles de herramientas ya inservibles, fusionando caminos redundantes en un único estado visitado.

## Prueba de meta

$$Goal(s) \iff \forall\, e \in \text{Estaciones\_críticas} : E[e] = \text{ONLINE}$$

Esto se lee así: el estado $s$ es un estado meta si y solo si, para cada una de las estaciones críticas de la instalación, la variable lógica del entorno que representa esa estación indica que está en línea (activa). Es decir, la misión se cumple cuando todas las estaciones críticas de la instalación
quedan en estado operativo (en línea) al mismo tiempo. La misión se verifica sobre el estado
final del mundo, no sobre haber ejecutado una lista de tareas.

**¿Las puertas y los paneles son parte de la meta o solo medios?**

Las puertas y los paneles son estrictamente medios para alcanzar un fin, no la meta en sí misma.
- Las puertas son obstáculos del mapa que restringen el movimiento. Abrirlas con su llave correspondiente es un requisito operativo para habilitar el tránsito del robot entre zonas, pero no aporta valor directo al éxito de la misión si el robot puede encontrar otra ruta óptima que evite cruzarlas.
- Los paneles son dependencias técnicas. Repararlos es necesario para habilitar la activación de una estación, pero reparar un panel que no está conectado a ninguna estación crítica requerida por la meta es un desperdicio de materiales y energía que un plan de costo mínimo debe evitar.

El agente asume el fin (las estaciones críticas en estado operativo) y calcula los medios necesarios (desbloquear accesos, reparar paneles intermedios) para hacer ese fin físicamente posible.

**Por qué la meta se verifica sobre el estado del mundo y no sobre las tareas**

1. **Preserva la autonomía y flexibilidad del agente.** Es un principio de diseño fundamental definir las metas de acuerdo con lo que realmente se quiere lograr en el entorno, y no según cómo creemos que el agente debe comportarse. Si se definiera el objetivo como "hacer las tareas A, B y C", se estaría forzando al robot a seguir una secuencia predeterminada. Al verificar la meta sobre el estado del mundo, se le da libertad al algoritmo de búsqueda para encontrar atajos creativos, optimizar el uso de la batería u omitir acciones redundantes que los diseñadores no habrían anticipado.

2. **Evita la explosión combinatoria en la lista de explorados.** Si la meta consistiera en verificar una lista de tareas ejecutadas, el estado del agente tendría que almacenar variables del historial (como "tarea 1 completada"). Esto rompería la separación entre el Estado y el Nodo, y la lista de explorados trataría a dos situaciones físicamente idénticas como estados distintos solo porque se realizaron en diferente orden, impidiendo detectar transposiciones y haciendo colapsar el árbol de búsqueda por falta de memoria.

3. **Garantiza una verificación física real.** El simulador evalúa retrospectivamente el estado físico de las variables al final de la ejecución del plan. Lo único que se comprueba es que las estaciones queden físicamente en estado seguro. Si el agente ejecutara todos los pasos de una lista de tareas pero un factor físico (como la falta de batería para el último paso, o una condición omitida) impidiera que la estación meta se active, la misión habría fallado igualmente. El éxito se mide en el resultado real en el mundo, no en la cantidad de pasos ejecutados por el robot.

## Función de costo

$$g(n) = \sum_{i=1}^{k} \text{costo}(a_i)$$

Esta fórmula dice que el costo acumulado del nodo $n$ es la suma de los costos de cada una de las $k$ acciones $a_1, a_2, \dots, a_k$ que forman el plan parcial desde el estado inicial hasta llegar a $n$. Cada vez que se aplica una acción nueva, su costo se suma al costo acumulado del nodo padre; así $g(n)$ crece de forma monótona a medida que el plan avanza.

El costo acumulado de un plan es la suma de los costos oficiales de cada una
de las acciones que lo componen, desde el estado inicial hasta el nodo
actual. Todos los costos son estrictamente no negativos:
- **Moverse:** el costo dinámico de energía definido por el corredor utilizado.
- **Recoger / soltar objetos:** el costo de manipulación definido en la configuración del escenario.
- **Interactuar (abrir puerta, reparar, activar, recargar):** el costo de operación definido por el escenario para cada interacción.

Debe ser la suma de los costos oficiales del escenario, no el número de pasos.

**Por qué minimizar pasos no es lo mismo que minimizar costo**

En este escenario existen corredores "baratos" y "caros" que consumen diferentes niveles de batería, a diferencia de un puzzle simple donde cada acción cuesta lo mismo. Si el agente intentara minimizar solo la cantidad de pasos, trataría a todos los movimientos por igual, asumiendo que dar un paso por un corredor de costo alto es igual de preferible que darlo por uno de costo bajo.

Si el robot se guiara únicamente por el menor número de acciones, podría elegir un plan de pocos pasos pero muy costoso en energía, en lugar de un plan con más pasos pero mucho más barato en consumo. Esto no solo produciría un plan más costoso, sino que físicamente podría llevar al fracaso de la misión al agotar la batería antes de alcanzar una estación de recarga.

Un algoritmo que minimiza solo el número de pasos únicamente es óptimo cuando todas las acciones cuestan lo mismo. Como en este entorno los costos son heterogéneos, la única manera de garantizar un plan de consumo mínimo es usar un algoritmo sensible al costo acumulado real, no al número de pasos.

## Estrategia de búsqueda

### Algoritmo seleccionado para la búsqueda: Búsqueda de Costo Uniforme (UCS)

La estrategia seleccionada es **Uniform-Cost Search (UCS)** implementada como
**Graph Search**. La elección se basa en las propiedades reales del problema:
los corredores tienen costos de movimiento diferentes y las operaciones
también tienen costos definidos por el escenario. Por eso, minimizar el
número de acciones no equivale a minimizar el costo total.

UCS mantiene una frontera `OPEN` ordenada por el costo acumulado `g(n)` y
expande primero el nodo con menor costo de camino. La prueba de meta se hace
**al extraer un nodo de `OPEN`**, no al generarlo. Bajo costos no negativos y
una formulación correcta del espacio de estados, el primer nodo meta extraído
es una solución de costo mínimo.

El flujo de decisión es:

```text
Estado inicial
      ↓
generar acciones
      ↓
Applicable(s)
      ↓
Result(s,a)
      ↓
canonicalizar
      ↓
OPEN ordenada por g(n)
      ↓
extraer menor g(n)
      ↓
 ¿Goal(s)?
  ↙       ↘
sí         no
↓           ↓
plan       expandir
            ↓
          repetir
```

La búsqueda no utiliza un plan memorizado. El plan se construye dinámicamente
a partir del escenario recibido, generando sucesores y comparando sus costos.
`CLOSED` se utiliza para evitar reexplorar configuraciones equivalentes o
dominadas y `parent` permite reconstruir la secuencia final de acciones.


### Discusión de propiedades

**Completitud.** La búsqueda de costo uniforme tiene garantía de completitud en este entorno bajo tres condiciones que se cumplen en este diseño:
1. El número de acciones posibles por estado es finito (derivado de un conjunto acotado de acciones aplicables).
2. Todos los costos de las acciones son positivos y mayores a un valor mínimo fijo (esto evita que el algoritmo quede atrapado en un ciclo de costo acumulado cero).
3. El espacio de estados es finito: si no existe un camino viable hacia la meta (por ejemplo, si el robot se queda sin batería en una zona sin estación de recarga), el algoritmo vaciará la frontera de búsqueda y reportará con certeza que no hay solución, en lugar de entrar en un bucle infinito.

**Optimalidad (¿la prueba de meta se hace al extraer o al generar?).** La búsqueda de costo uniforme es óptima porque la prueba de meta se realiza únicamente al extraer un nodo de la frontera de búsqueda, no al generarlo. Si se evaluara la meta en el momento de generar un nodo hijo, el algoritmo podría devolver un camino más corto en pasos pero más costoso en energía.

Por ejemplo: si el robot puede llegar a la meta por un corredor directo caro en un solo paso, o por una ruta alternativa de varios pasos baratos que en total cuesta menos, evaluar la meta apenas se genera el nodo detendría la búsqueda en la primera opción (más cara). Al evaluar la meta solo cuando el nodo se extrae de la frontera ordenada por costo, se garantiza que el primer nodo meta encontrado sea el de menor costo acumulado de toda la frontera.

**Costo de camino.** La función de evaluación usa exclusivamente el costo de camino acumulado del nodo, que se guarda como un dato del Nodo (no del Estado) y se actualiza sumando el costo de cada acción al costo acumulado del nodo padre. La frontera se implementa como una cola ordenada de menor a mayor costo acumulado.

**Tiempo y espacio.** La complejidad en el peor caso depende del número de acciones posibles por estado y de la relación entre el costo del plan óptimo y el costo mínimo de una acción individual: mientras más "ramificado" sea el problema y más barata sea la acción mínima, más nodos hay que explorar.

Muchos suponen erróneamente que esa ramificación está limitada por el grado de conectividad del mapa (por ejemplo, que una zona solo se conecta a otras dos o tres). Esto es falso: la verdadera ramificación peligrosa está determinada por la cantidad de acciones lógicas que el agente genera como sucesores en cada estado. Si el generador de sucesores permite recoger o soltar cualquier objeto en cualquier zona sin un propósito inmediato, esa ramificación se multiplica exponencialmente por la combinatoria de ubicaciones de objetos. Al restringir la generación de DROP solo a los casos de saturación de carga, se reduce drásticamente la ramificación efectiva de la búsqueda, permitiendo que la memoria y el tiempo de cómputo se mantengan en niveles mínimos.

**Cuándo se rompen las garantías del algoritmo:**
- **Costos cero o negativos:** si recoger o soltar un objeto tuviera costo cero, el robot podría entrar en un bucle infinito de manipulación repetitiva sin incrementar el costo del camino. Si los costos fueran negativos, se rompería la suposición de que el costo de camino crece de forma constante, impidiendo que el primer nodo meta extraído sea el óptimo.
- **Estados mal normalizados:** si dos estados que representan la misma situación física (por ejemplo, los mismos objetos en el mismo lugar pero representados en listas con distinto orden) no generan la misma firma, la lista de explorados no los reconocerá como repetidos. El algoritmo volverá a explorar rutas redundantes y la frontera crecerá de forma exponencial, agotando la memoria.
- **La frontera nunca se vacía:** si el problema no tiene solución física (por falta de batería o de materiales) pero el agente no detecta los ciclos debido a un mal diseño de la lista de explorados, la frontera jamás se vaciará y el algoritmo seguirá expandiendo nodos indefinidamente hasta agotar la memoria.

**Graph Search exige una lista de estados explorados sobre estados canónicos. Cómo se evita reexplorar la misma situación física:**

Para garantizar la máxima eficiencia, el algoritmo implementa una búsqueda sobre grafos con una lista de estados explorados. El siguiente diagrama resume el flujo de decisión aplicado a cada estado sucesor:

```text
                                  ┌─────────────────────────┐
                                  │   Estado siguiente      │
                                  └────────────┬────────────┘
                                               │
                                      [ Normalizar estado ]
                                               │
                                               ▼
                                ┌─────────────────────────────┐
                                │ ¿Ya está explorado o en la  │
                                │ frontera de búsqueda?       │
                                └──────────────┬──────────────┘
                                               │
                       ┌───────────────────────┴───────────────────────┐
                    Sí │                                               │ No
                       ▼                                               ▼
         ┌───────────────────────────┐                   ┌───────────────────────────┐
         │ ¿La ruta nueva es más     │                   │  Añadir a la lista de     │
         │ barata que la registrada? │                   │  explorados / frontera    │
         └─────────────┬─────────────┘                   └───────────────────────────┘
                       │
             ┌─────────┴─────────┐
          Sí │                No │
             ▼                   ▼
     [ Actualizar y      [ Descartar el
       reemplazar el       nodo nuevo ]
       camino anterior ]
```

Para evitar que el agente explore repetidamente la misma situación física por llegar a ella con distintos órdenes de acciones (transposiciones), la lista de explorados sigue estas reglas de diseño:

- **Evaluación de estados normalizados:** cada nodo que se extrae de la frontera tiene un estado con una representación fija e inmutable. La lista de explorados guarda únicamente estas firmas únicas, lo que permite consultas casi instantáneas.
- **Sustitución de rutas:** si un estado que ya está en la frontera de búsqueda es alcanzado por un nuevo camino estrictamente más barato que el registrado antes, el algoritmo no lo ignora: actualiza el costo acumulado, reemplaza el nodo en la cola de prioridad por la versión más barata y reasigna su referencia al nuevo nodo origen. Si el nuevo camino es más costoso, se descarta de inmediato.

Al separar estrictamente la física del estado de la historia del nodo, y normalizar cada estado tras cada transición, el agente colapsa eficientemente el árbol de búsqueda en un grafo acotado, resolviendo el escenario en el menor tiempo posible sin comprometer la optimalidad del plan final.

## Batería como recurso

La batería sí va en el estado. Eso no implica explorar todos los paseos que
solo gastan energía. Si dos caminos llegan a la misma configuración del mundo
(zona, carga, suelo, entorno) y uno trae más batería residual a un costo
menor o igual, el otro no puede mejorar ningún plan futuro: está dominado.
Tratar cada nivel de batería como un mundo distinto, sin esa observación,
hace que la búsqueda recorra desvíos inútiles hasta agotar memoria. Justifique
cómo la lista de explorados aprovecha (o no) esta dominancia.

**Cómo la lista de explorados aprovecha esta dominancia**

Para aprovechar esta dominancia, la lista de explorados no debe comparar los estados completos de forma exacta ("todo o nada"). En su lugar, debe registrar por separado la configuración del mundo y el nivel de batería con el que fue visitada.

Se puede pensar el estado completo como formado por dos partes: la configuración del mundo (posición del robot, inventario, objetos en el suelo y estado lógico del entorno) por un lado, y el nivel de batería por otro. La lista de explorados se organiza entonces como una tabla que asocia cada configuración del mundo con el máximo nivel de batería residual con el que se ha expandido esa configuración hasta el momento.

Gracias a que la búsqueda de costo uniforme extrae los nodos de la frontera en orden creciente de costo acumulado, cualquier nodo con la misma configuración del mundo que se extraiga más tarde tendrá, por definición, un costo acumulado mayor o igual al anterior. Por eso, cuando el algoritmo extrae un nodo, evalúa lo siguiente antes de expandirlo:

- **Si la configuración del mundo no está registrada:** es la primera vez que se alcanza esa configuración física. Se registra junto con su batería actual y se procede a expandirla.
- **Si la configuración del mundo ya está registrada, con cierto nivel máximo de batería:**
  - Si la batería del nodo actual es menor o igual a la registrada, el nodo está completamente dominado (ofrece igual o menor energía a un costo igual o mayor), así que se descarta y se poda de inmediato, sin expandir sus sucesores.
  - Si la batería del nodo actual es mayor a la registrada, aunque el costo acumulado sea mayor, el nodo trae más energía residual que podría ser la única capaz de permitir acciones costosas más adelante en el mapa. En ese caso, se actualiza el registro con la nueva batería y se procede a expandirlo.

**Impacto en el espacio de estados**

Este diseño elimina de raíz la multiplicación de caminos redundantes y desvíos inútiles. El robot ya no gasta memoria simulando trayectorias donde deambula sin sentido gastando energía, porque cualquier intento de revisitar una configuración con menor batería y peor costo es interceptado y descartado de forma casi instantánea por el chequeo de dominancia.

## Formulación y tamaño del espacio (obligatorio)

El mapa visible es pequeño. El espacio de estados no lo es, si se formula
mal. Responda con sus palabras:

**¿Por qué «5 zonas, ~10 objetos, capacidad 3» puede generar millones de nodos en una búsqueda ingenua?**

En un diseño de búsqueda ingenuo, el tamaño del espacio de estados sufre una explosión combinatoria extrema por la forma en que se representan los objetos y el inventario. Si cada uno de los 10 objetos se considera único e identificable individualmente, y el robot puede llevar hasta 3 de ellos, el número de combinaciones posibles para distribuir los objetos entre las 5 zonas y el inventario es enorme: existen más de 60 millones de combinaciones solo para la distribución física de los objetos. Si a esto se le suman las 5 posibles posiciones del robot y los distintos niveles de batería, el espacio de estados total supera los cientos de millones de configuraciones posibles. Un algoritmo de búsqueda de costo uniforme ingenuo, al explorar rutas redundantes y paseos circulares sin un estado normalizado, generará y guardará millones de nodos en la frontera antes de acercarse siquiera a la meta, agotando la memoria.

**¿Qué papel tiene DROP en esa explosión?**

La acción de soltar objetos es el principal cuello de botella. El simulador permite soltar un objeto en cualquier zona siempre que el robot lo lleve en su carga. Si el agente genera esa acción de forma permisiva en cada estado en el que el robot carga algo, la cantidad de acciones posibles por estado crece de manera descontrolada. El espacio de estados deja de ser "un mapa simple de 5 zonas" y se convierte en la combinatoria de dónde quedó abandonado cada objeto. El algoritmo desperdicia tiempo simulando ramas inútiles donde el robot deambula tirando y recogiendo objetos en zonas irrelevantes, sin ningún progreso real hacia la meta.

**¿Qué podas o abstracciones se aplicaron y por qué no pierden el óptimo?**

Se aplicaron tres estrategias:
- **Agregación de objetos:** los materiales equivalentes (como fusibles o placas) no se distinguen individualmente con identificadores únicos; se modelan mediante contadores por tipo en el estado, eliminando millones de permutaciones físicamente idénticas.
- **Restricción estricta de DROP:** el agente solo genera esta acción si hay saturación de carga, es decir, cuando el robot necesita liberar peso para poder recoger un objeto prioritario.
- **Poda de objetos "muertos":** una vez que un sistema o puerta fue reparado o abierto de forma permanente, las llaves o herramientas específicas requeridas para esa única tarea pierden toda utilidad y se eliminan del estado de búsqueda.

Estas podas no hacen perder la solución óptima porque, en el simulador, viajar con carga no penaliza el consumo de batería (el costo de moverse depende solo del corredor), y toda acción de manipulación tiene un costo oficial estrictamente positivo. Cualquier plan que decida soltar un objeto para luego volver a recogerlo sin una necesidad física de peso acumulará un costo mayor. El plan óptimo siempre preferirá llevar los objetos guardados de forma continua. Por lo tanto, restringir la acción de soltar objetos solo a los casos de saturación de carga garantiza que nunca se pierda un plan óptimo.

**¿Por qué no es solución subir la capacidad, bajar las estaciones o ignorar la batería?**

Estas alteraciones modifican las constantes físicas del escenario, no el modelo del agente, y son un error de formulación grave:
- **Falta de generalización:** el escenario es la fuente de verdad y será evaluado con mapas, recursos, posiciones y capacidades completamente distintas. Si el agente depende de una capacidad alta para no explotar, colapsará de inmediato al probarse con restricciones de carga estrictas.
- **Violación de las reglas del simulador:** ignorar la batería o eliminar estaciones rompe las reglas físicas que el simulador hace cumplir. Si el agente genera un plan asumiendo batería infinita, el simulador rechazará el plan en el primer paso donde la energía no alcance, deteniendo la simulación con un fallo.
- **El problema real está en el modelo:** la ineficiencia no se debe a que el problema sea físicamente grande, sino a un generador de sucesores demasiado permisivo y a un estado mal normalizado. El diseño correcto consiste en resolver un entorno restrictivo optimizando la representación interna del agente, no facilitando el escenario.