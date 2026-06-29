# Diseño del esquema de una criptomoneda basada en tecnología blockchain para realizar donaciones

**Autor:** Act. André Marx Puente Arévalo  
**Asesor:** Mtro. José De Jesús Ángel Ángel  
**Nombre del proyecto:** Diseño del esquema de una criptomoneda basada en tecnología blockchain para realizar donaciones  
**Objetivo académico:** Proyecto Aplicativo para titulación de Maestría en Tecnologías de Información e Inteligencia Analítica  
**Universidad:** Universidad Anáhuac

## Objetivo del proyecto

Este proyecto simula el funcionamiento completo de una criptomoneda enfocada en donaciones. La moneda simulada, HopeCoin, permite representar cómo una red blockchain puede registrar transferencias digitales hacia organizaciones sin fines de lucro, validar transacciones, agruparlas en bloques, minarlas mediante prueba de trabajo y sincronizar el estado de la cadena entre diferentes nodos.

La simulación cubre el ciclo principal de una criptomoneda desde sus fundamentos criptográficos hasta su ejecución distribuida. El sistema genera billeteras digitales, crea direcciones públicas, calcula balances, firma transacciones y valida que cada operación provenga realmente de la billetera emisora. Para las firmas digitales se utiliza ED25519, y antes de firmar o verificar los datos se genera un hash SHA-512. Esto permite demostrar la relación entre identidad criptográfica, integridad de datos y autorización de transacciones.

Cada transacción enviada desde la interfaz queda primero en el mempool, que funciona como el conjunto de transacciones pendientes de confirmación. Después, un nodo puede iniciar el proceso de minado. El minado usa prueba de trabajo: el sistema busca un nonce que produzca un hash válido para el bloque, de acuerdo con la dificultad configurada. Cuando un nodo encuentra un hash que cumple la condición requerida, publica el bloque, las transacciones se agregan a la blockchain y el minero recibe una recompensa simulada.

El proyecto también permite levantar una red peer-to-peer. Esta modalidad permite conectar varias computadoras dentro de la misma red WiFi, o usar PubNub como transporte alterno cuando la red local o el firewall bloquean conexiones entrantes. En la modalidad distribuida, cada participante ejecuta su propio backend y su propia UI; las transacciones, el mempool, el estado de minado y los bloques se sincronizan entre nodos para simular una competencia real de minado.

## Requisitos

Este proyecto requiere explícitamente:

- Python 3.8.18
- Node.js y npm para ejecutar la interfaz web en React
- Conexión a internet si se usa la modalidad P2P con PubNub
- Varias computadoras en la misma red WiFi si se usa la modalidad P2P por sockets TCP locales

Verifica la versión de Python antes de instalar dependencias:

```bash
python3 --version
```

La salida esperada debe ser:

```bash
Python 3.8.18
```

## Instalación del backend

Desde la raíz del proyecto, crea y activa un entorno virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

Después instala las librerías declaradas en `requirements.txt`:

```bash
python3 -m pip install -r requirements.txt
```

Cada vez que abras una nueva terminal para trabajar con el backend, primero activa el entorno virtual:

```bash
source venv/bin/activate
```

## Instalación del frontend

La interfaz está en la carpeta `frontend_ui`. Si es la primera vez que se ejecuta, instala sus dependencias:

```bash
cd frontend_ui
npm install
```

Este comando crea la carpeta `frontend_ui/node_modules` en la computadora donde se ejecuta el proyecto. Esa carpeta no se debe subir al repositorio porque puede ser muy grande y depende del sistema donde se instale. Lo que sí se versiona es `package.json` y `package-lock.json`; con esos archivos, cualquier persona que descargue el repositorio puede reconstruir `node_modules` ejecutando `npm install`.

## Ejecutar el proyecto sin peer-to-peer

Esta modalidad levanta un solo backend y una sola interfaz web. Es útil para revisar la blockchain, crear transacciones, minar bloques y probar el flujo completo sin conectar otras computadoras. El backend inicializa el servicio P2P en modo servidor, pero si no conectas otros peers puedes usarlo como una ejecución local de una sola instancia.

### Correr la aplicación y API

Primero estar seguro de activar el ambiente virtual:

```bash
source venv/bin/activate
```

Ejecuta el backend:

```bash
python3 -m backend.app
```

Por defecto, la API queda disponible en:

```text
http://localhost:5050
```

Puedes verificar que el backend esté activo con:

```bash
curl http://localhost:5050/health
```

En la configuración actual, el nodo servidor carga datos simulados automáticamente porque `AUTO_SEED_ROOT=True` es el valor por defecto. Si necesitas iniciar el backend sin datos precargados, ejecuta:

```bash
AUTO_SEED_ROOT=False python3 -m backend.app
```

### Seed the backend with data

Si se desea ejecutar con datos simulados, primero estar seguro de activar el ambiente virtual:

```bash
source venv/bin/activate
```

Después ejecuta:

```bash
export SEED_DATA=True && python3 -m backend.app
```

Este comando deja explícita la carga de bloques y transacciones simuladas para que la UI tenga información desde el inicio.

### Run the frontend

En otra terminal, con el backend todavía corriendo, entra a la carpeta del frontend:

```bash
cd frontend_ui
```

Ejecuta:

```bash
npm run start
```

La interfaz web normalmente abrirá en:

```text
http://localhost:3000
```

Si el navegador no se abre automáticamente, entra manualmente a esa URL.

## Tests

La carpeta `backend/tests` contiene pruebas automatizadas para validar las piezas principales del proyecto:

- Pruebas de blockchain: validan la creación del bloque génesis, el minado de bloques, la referencia al hash anterior, la prueba de trabajo, la validación de bloques y el reemplazo de cadenas.
- Pruebas de transacciones: revisan que las transacciones respeten el balance disponible, que sus salidas sumen correctamente, que las firmas sean válidas y que las recompensas de minería cumplan las reglas esperadas.
- Pruebas de billetera: validan la generación de billeteras, balances y firmas digitales.
- Pruebas de utilidades criptográficas: revisan el hash SHA-512 usado por el proyecto y la conversión de hashes hexadecimales a binario para validar la dificultad de minado.

### Correr Pruebas

Primero estar seguro de activar el ambiente virtual:

```bash
source venv/bin/activate
```

Ejecuta:

```bash
python3 -m pytest backend/tests
```

## Interfaz de usuario

La UI está construida en React y se conecta al backend mediante la variable `REACT_APP_API_BASE_URL`. Si no se configura esta variable, la UI usa por defecto `http://localhost:5050`.

La interfaz está organizada en cuatro secciones principales.

### Inicio

La pantalla de inicio funciona como tablero general de HopeCoin. Muestra la billetera activa del nodo, su dirección pública y el balance disponible. También presenta un resumen rápido del estado de la red local del backend: cuántos bloques existen actualmente en la blockchain y cuántas transacciones están esperando en el mempool.

Desde esta vista se puede navegar a las acciones principales: consultar la blockchain, realizar una transacción o ir al grupo de transacciones para minar. La pantalla se actualiza de forma periódica para reflejar cambios recientes en el balance, bloques y transacciones pendientes.

### Blockchain

La sección Blockchain permite visualizar el estado actual de la cadena de bloques. Muestra los bloques minados, sus hashes, la referencia al bloque anterior, la información de dificultad, nonce y las transacciones incluidas en cada bloque.

Esta sección sirve para comprobar que los bloques quedan encadenados correctamente: cada bloque conserva el hash del bloque anterior y su propio hash se recalcula con los datos del bloque. También permite observar cómo crece la cadena después de minar nuevas transacciones.

### Realizar transacciones

La sección Realizar transacciones permite enviar HopeCoins a organizaciones sin fines de lucro simuladas y certificadas dentro del proyecto. La UI presenta una lista de organizaciones con su nombre, área de apoyo, misión y dirección de billetera.

El usuario selecciona una organización, define el monto a donar y envía la transacción. El backend valida que la billetera tenga saldo disponible, genera la transacción, firma la operación con la llave privada de la billetera emisora y coloca la transacción en el mempool.

Mientras una transacción está en el mempool, el saldo correspondiente queda reservado. Por eso la UI muestra balance total, monto reservado en mempool y balance disponible. La transacción todavía no forma parte definitiva de la blockchain hasta que se mine un bloque que la incluya.

### Minar transacciones

La sección Minar transacciones muestra el estado del mempool y permite iniciar la competencia de minado. Ahí se ven las transacciones pendientes antes de consolidarse en el siguiente bloque.

Cuando el usuario presiona el botón para competir por el minado, el backend agrega una transacción de recompensa para el minero y comienza la prueba de trabajo. La UI muestra el estado del proceso: nodo local, número de peers conectados, dificultad, nonce actual, hash actual, mineros activos y ganador cuando se encuentra un bloque válido.

Si el proyecto se ejecuta en modo P2P, varios nodos pueden competir al mismo tiempo. El primer nodo que encuentra un hash válido publica el bloque y el resto de nodos detiene su minado, sincroniza la blockchain y actualiza el mempool.

## Red peer-to-peer en WiFi local

La red P2P permite que varias computadoras participen en la simulación. Cada computadora debe ejecutar su propio backend y su propia UI. El backend mantiene la billetera local, recibe o transmite transacciones, participa en el minado y sincroniza bloques con los demás nodos.

Existen dos formas de ejecutar la red:

- PubNub: recomendado para demos porque evita problemas de firewall o permisos de red. Todos los nodos usan un canal compartido y se comunican mediante conexiones salientes a internet.
- Sockets TCP en WiFi local: usa conexiones directas dentro de la misma red WiFi. Requiere que la computadora raíz acepte conexiones entrantes en los puertos del backend y del P2P.

### Modalidad P2P con PubNub

En PubNub todos los nodos deben usar exactamente el mismo `P2P_CLOUD_CHANNEL`. Puedes cambiar el nombre del canal para cada clase o demostración; lo importante es que el nodo raíz y todos los peers usen el mismo valor.

#### Ejecutar el nodo raíz con PubNub

En la computadora que actuará como nodo raíz, desde la raíz del proyecto:

```bash
source venv/bin/activate
HOST=0.0.0.0 PORT=5050 P2P_MODE=server P2P_TRANSPORT=pubnub P2P_CLOUD_CHANNEL=hopecoin-clase python3 -m backend.app
```

El nodo raíz coordina la sincronización del estado. En este modo, el backend carga datos simulados automáticamente para facilitar la demo. Si quieres iniciar sin datos precargados, agrega:

```bash
AUTO_SEED_ROOT=False
```

Ejemplo:

```bash
HOST=0.0.0.0 PORT=5050 P2P_MODE=server P2P_TRANSPORT=pubnub P2P_CLOUD_CHANNEL=hopecoin-clase AUTO_SEED_ROOT=False python3 -m backend.app
```

#### Ejecutar la UI del nodo raíz

En otra terminal de la misma computadora:

```bash
cd frontend_ui
HOST=0.0.0.0 PORT=3000 REACT_APP_API_BASE_URL=http://localhost:5050 npm run start
```

#### Ejecutar un nodo peer con PubNub

En cada computadora participante, desde la raíz del proyecto:

```bash
source venv/bin/activate
HOST=0.0.0.0 PORT=5051 P2P_MODE=peer P2P_TRANSPORT=pubnub P2P_CLOUD_CHANNEL=hopecoin-clase python3 -m backend.app
```

Si vas a ejecutar más de un backend en la misma computadora, cambia el puerto HTTP de cada peer para evitar choques:

```bash
HOST=0.0.0.0 PORT=5052 P2P_MODE=peer P2P_TRANSPORT=pubnub P2P_CLOUD_CHANNEL=hopecoin-clase python3 -m backend.app
```

#### Ejecutar la UI de cada peer

En cada computadora peer, abre otra terminal y apunta la UI al backend local de esa computadora:

```bash
cd frontend_ui
HOST=0.0.0.0 PORT=3001 REACT_APP_API_BASE_URL=http://localhost:5051 npm run start
```

Si el peer usa otro puerto de backend, ajusta `REACT_APP_API_BASE_URL`. Por ejemplo, para un backend en `5052`:

```bash
HOST=0.0.0.0 PORT=3002 REACT_APP_API_BASE_URL=http://localhost:5052 npm run start
```

En modo PubNub, los logs pueden mostrar mensajes como `PubNub enviara SYNC_STATE en N partes` o `PubNub rearma SYNC_STATE`. Esto es normal cuando el estado de la blockchain o del mempool es grande: el backend comprime y divide el mensaje para enviarlo por partes.

### Modalidad P2P con sockets TCP en WiFi local

Esta modalidad usa sockets TCP directos entre las computadoras conectadas a la misma red WiFi. La computadora raíz debe estar accesible desde las demás computadoras.

#### 1. Obtener la IP local del nodo raíz

En macOS, puedes obtener la IP local con:

```bash
ipconfig getifaddr en0
```

Si esa interfaz no corresponde a tu WiFi, inicia el backend y revisa las URLs que imprime en consola como `URL HTTP LAN`. También puedes consultar:

```bash
curl http://localhost:5050/network/status
```

En los comandos siguientes, reemplaza `TU_IP_LOCAL_DEL_SERVIDOR` por la IP real del nodo raíz.

#### 2. Iniciar el backend del nodo raíz

En la computadora raíz:

```bash
source venv/bin/activate
HOST=0.0.0.0 PORT=5050 P2P_MODE=server P2P_SOCKET_HOST=0.0.0.0 P2P_SOCKET_PORT=17000 P2P_MINING_DIFFICULTY=20 python3 -m backend.app
```

El backend HTTP queda en el puerto `5050` y el socket P2P queda en el puerto `17000`.

Verifica localmente que el backend responda:

```bash
curl http://localhost:5050/health
```

Desde otra computadora en la misma WiFi, verifica la IP LAN del nodo raíz:

```bash
curl http://TU_IP_LOCAL_DEL_SERVIDOR:5050/health
curl http://TU_IP_LOCAL_DEL_SERVIDOR:5050/network/diagnostics
```

Si `localhost` responde en la computadora raíz pero la IP LAN no responde desde otra computadora, el problema normalmente está en la IP elegida, el firewall, permisos de Python, VPN o aislamiento de clientes en la red WiFi.

#### 3. Iniciar la UI del nodo raíz

En otra terminal de la computadora raíz:

```bash
cd frontend_ui
HOST=0.0.0.0 PORT=3000 REACT_APP_API_BASE_URL=http://localhost:5050 npm run start
```

Si otra computadora va a abrir la UI servida por el nodo raíz, puedes apuntarla a la IP LAN:

```bash
HOST=0.0.0.0 PORT=3000 REACT_APP_API_BASE_URL=http://TU_IP_LOCAL_DEL_SERVIDOR:5050 npm run start
```

#### 4. Iniciar backends peer

En cada computadora participante:

```bash
source venv/bin/activate
HOST=0.0.0.0 PORT=5051 P2P_MODE=peer P2P_ROOT_HOST=TU_IP_LOCAL_DEL_SERVIDOR P2P_ROOT_PORT=17000 ROOT_HTTP_HOST=TU_IP_LOCAL_DEL_SERVIDOR ROOT_HTTP_PORT=5050 P2P_MINING_DIFFICULTY=20 python3 -m backend.app
```

Cada peer usa:

- `PORT`: puerto HTTP local de su backend.
- `P2P_MODE=peer`: indica que este backend se conectará a un nodo raíz.
- `P2P_ROOT_HOST`: IP LAN del nodo raíz.
- `P2P_ROOT_PORT`: puerto P2P del nodo raíz, normalmente `17000`.
- `ROOT_HTTP_HOST` y `ROOT_HTTP_PORT`: dirección HTTP del nodo raíz para sincronización inicial.
- `P2P_MINING_DIFFICULTY`: dificultad usada en la competencia de minado.

#### 5. Iniciar la UI de cada peer

En cada computadora participante, en otra terminal:

```bash
cd frontend_ui
PORT=3001 REACT_APP_API_BASE_URL=http://localhost:5051 npm run start
```

Si el backend del peer usa otro puerto, actualiza la URL. Por ejemplo:

```bash
PORT=3002 REACT_APP_API_BASE_URL=http://localhost:5052 npm run start
```

### Flujo recomendado para la simulación P2P

1. Inicia el backend del nodo raíz.
2. Inicia la UI del nodo raíz.
3. Inicia el backend de cada peer.
4. Inicia la UI de cada peer apuntando a su propio backend local.
5. Abre la sección Realizar transacciones en cualquier nodo.
6. Envía una donación simulada a una organización sin fines de lucro.
7. Verifica que la transacción aparezca en el mempool de los nodos conectados.
8. Entra a Minar transacciones desde dos o más nodos.
9. Presiona Competir para minar.
10. Observa nonce, hash, dificultad, mineros activos y ganador.
11. Cuando un nodo encuentre el hash válido, el bloque se agrega a la blockchain y los demás nodos sincronizan el resultado.

Para una demo con varios nodos, usa el mismo canal PubNub o la misma IP del servidor raíz, según la modalidad elegida. Si el minado tarda demasiado o termina demasiado rápido, ajusta `P2P_MINING_DIFFICULTY`; valores entre `18` y `22` suelen ser útiles para demostraciones de 1 a 2 minutos, dependiendo de la computadora.

### Diagnóstico rápido de red local

Si usas sockets TCP y un peer no logra conectarse:

- Confirma que el nodo raíz imprime `HTTP escuchara en 0.0.0.0:5050`.
- Confirma que el nodo raíz imprime `P2P escuchara en 0.0.0.0:17000`.
- Desde el peer, prueba `curl http://TU_IP_LOCAL_DEL_SERVIDOR:5050/health`.
- Evita usar `PORT=5000` y `P2P_SOCKET_PORT=7000` en macOS, porque pueden chocar con AirPlay, servicios del sistema o reglas de firewall.
- Acepta conexiones entrantes para Python en macOS o desactiva temporalmente el firewall durante la prueba.
- Verifica que todas las computadoras estén en la misma red WiFi y que la red no tenga aislamiento entre clientes.

Si la red local sigue bloqueando conexiones, usa la modalidad PubNub.
