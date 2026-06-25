**Versión de Python**
Python 3.8.18

**Crear un ambiente virtual**
```
python -m venv venv
```

**Activar el ambiente virtual**
```
source venv/bin/activate
```

**Instalar todos los paquetes**
```
pip3 install -r requerimientos.txt
```

**Para ejecutar los módulos en la terminal**
```
python3 -m backend.blockchain.block
```

**Correr Pruebas**
Primero estar seguro de activar el ambiente virtual
```
python3 -m pytest backend/tests
```

**Correr la aplicación y API**
Primero estar seguro de activar el ambiente virtual
```
python3 -m backend.app
```

**Correr un par de instancias**
Primero estar seguro de activar el ambiente virtual
```
export PEER=True && python3 -m backend.app
```

**Run the fronted**
In the frontend directory:
```
npm run start
```

**Seed the backend with data**
Primero estar seguro de activar el ambiente virtual
```
export SEED_DATA=True && python3 -m backend.app
```

**Red peer-to-peer en WiFi local**

La red usa sockets TCP de Python. Una computadora actua como nodo raiz y las demás se conectan como peers. Para que compitan realmente en el minado, cada participante debe ejecutar su propio backend y su propia UI apuntando a ese backend.

1. Obtener la IP local de la computadora que sera servidor raiz:
```
ipconfig getifaddr en0
```
Si usas otra interfaz de red, también puedes iniciar el backend y consultar `http://localhost:5050/network/status`.

2. Iniciar el nodo raiz en la computadora anfitriona:
```
HOST=0.0.0.0 PORT=5050 P2P_MODE=server P2P_SOCKET_HOST=0.0.0.0 P2P_SOCKET_PORT=17000 P2P_MINING_DIFFICULTY=20 python3 -m backend.app
```
El nodo raiz carga datos simulados automaticamente. Si quieres iniciarlo sin datos, agrega `AUTO_SEED_ROOT=False`.

Antes de abrir la UI, verifica que el backend responda:
```
curl http://localhost:5050/health
```
Desde otra computadora en la misma WiFi, verifica la IP LAN del nodo raiz:
```
curl http://TU_IP_LOCAL:5050/health
curl http://TU_IP_LOCAL:5050/network/diagnostics
```
Si `localhost` responde pero `TU_IP_LOCAL` no, la IP elegida no es la correcta o macOS/firewall esta bloqueando conexiones entrantes para Python.

No uses `curl http://TU_IP_LOCAL:5050/health` desde la misma Mac que corre el nodo raiz para decidir si la LAN funciona. En algunas configuraciones de macOS esa conexion hairpin hacia su propia IP LAN se resetea aunque `localhost` funcione. La IP LAN debe probarse desde la computadora peer.

Evita usar `PORT=5000` y `P2P_SOCKET_PORT=7000` en macOS para esta demo LAN. Esos puertos suelen chocar con AirPlay/servicios del sistema o reglas especiales de firewall: el sintoma típico es que `curl http://localhost:5000/health` funciona, pero `curl http://TU_IP_LOCAL:5000/health` responde `Connection reset by peer`.

Si el peer muestra `Connection reset by peer` pero en la terminal del nodo raiz no aparece ningun `GET /health`, `GET /blockchain` o `Conexion P2P entrante` desde la IP del peer, la conexion no esta llegando al backend raiz. En ese caso revisa estos puntos antes de seguir con el minado:
- El nodo raiz debe imprimirse como `HTTP escuchara en 0.0.0.0:5050` y `P2P escuchara en 0.0.0.0:17000`.
- El nodo raiz debe mostrar `Autoprueba P2P local OK`. Eso confirma que el proceso Python si acepta sockets P2P localmente.
- El peer debe mostrar `Preflight P2P PING/PONG OK` antes de intentar `HELLO`. Si no aparece, el problema esta antes del protocolo P2P: la red o el sistema esta cortando los bytes entre ambas computadoras.
- Usa la IP LAN que imprime el nodo raiz en `URL HTTP LAN`, no `127.0.0.1` ni una IP de otra interfaz.
- En macOS, acepta las conexiones entrantes para Python o desactiva temporalmente el firewall para la prueba.
- Desde la computadora peer, prueba `curl http://IP_RAIZ:5050/health`. Si eso falla, P2P tambien fallara porque el problema esta en red/IP/firewall, no en la blockchain.

3. Iniciar la UI del nodo raiz:
```
cd frontend_ui
HOST=0.0.0.0 PORT=3000 REACT_APP_API_BASE_URL=http://TU_IP_LOCAL:5050 npm start
```
Si estas probando la UI en la misma computadora del servidor raiz, tambien puedes usar:
```
HOST=0.0.0.0 PORT=3000 REACT_APP_API_BASE_URL=http://localhost:5050 npm start
```

4. En cada computadora participante, iniciar un backend peer. Cambia `TU_IP_LOCAL_DEL_SERVIDOR` por la IP del nodo raiz:
```
HOST=0.0.0.0 PORT=5051 P2P_MODE=peer P2P_ROOT_HOST=TU_IP_LOCAL_DEL_SERVIDOR P2P_ROOT_PORT=17000 ROOT_HTTP_HOST=TU_IP_LOCAL_DEL_SERVIDOR ROOT_HTTP_PORT=5050 P2P_MINING_DIFFICULTY=20 python3 -m backend.app
```

**Modo alterno si macOS/firewall bloquea la LAN**

Si desde la computadora peer `curl http://TU_IP_LOCAL:5050/health` devuelve `Connection reset by peer`, el sistema esta cortando conexiones entrantes hacia Python en el nodo raiz. Para la demo usa el transporte PubNub, que no requiere conexiones entrantes LAN porque ambos nodos abren conexiones salientes a internet. Usa el mismo `P2P_CLOUD_CHANNEL` en todos los nodos:

Nodo raiz:
```
HOST=0.0.0.0 PORT=5050 P2P_MODE=server P2P_TRANSPORT=pubnub P2P_CLOUD_CHANNEL=hopecoin-clase python3 -m backend.app
```

Nodo peer:
```
HOST=0.0.0.0 PORT=5051 P2P_MODE=peer P2P_TRANSPORT=pubnub P2P_CLOUD_CHANNEL=hopecoin-clase python3 -m backend.app
```

En modo PubNub, cada UI debe apuntar al backend local de esa misma computadora:
```
# UI del nodo raiz, en la Mac raiz
cd frontend_ui
HOST=0.0.0.0 PORT=3000 REACT_APP_API_BASE_URL=http://localhost:5050 npm start

# UI del peer, en la Mac peer
cd frontend_ui
HOST=0.0.0.0 PORT=3001 REACT_APP_API_BASE_URL=http://localhost:5051 npm start
```

Si el estado de la blockchain o del mempool es grande, el backend puede mostrar logs como
`PubNub enviara SYNC_STATE en N partes` y el peer luego mostrara
`PubNub rearma SYNC_STATE`. Es normal: el mensaje se comprime y se divide para evitar
el error `Request URI Too Long` de PubNub.

5. En cada computadora participante, iniciar su UI apuntando a su propio backend:
```
cd frontend_ui
PORT=3001 REACT_APP_API_BASE_URL=http://IP_LOCAL_DEL_PARTICIPANTE:5051 npm start
```

6. Flujo de simulacion:
- Todos abren su UI local.
- Alguien realiza una transaccion hacia una organizacion sin fines de lucro.
- La transaccion se transmite al mempool de todos los nodos conectados.
- Al menos dos integrantes entran a "Grupo de transacciones" y presionan "Competir para minar".
- La UI muestra nonce, hash, dificultad, mineros activos y ganador.
- El primer nodo que encuentre el hash valido publica el bloque, recibe la recompensa y todos los nodos lo ven en la blockchain.

Para una clase o demo con 5 nodos, usa la misma IP del servidor raiz en todos los peers y deja `P2P_SOCKET_PORT=17000`. Si el minado tarda demasiado o muy poco, ajusta `P2P_MINING_DIFFICULTY`; valores entre 18 y 22 suelen ser utiles para acercarse a 1-2 minutos segun la computadora.
