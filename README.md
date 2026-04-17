**Crear un ambiente virtual**
```
python3 -m venv blockchain-env
```

**Activar el ambiente virtual**
```
source blockchain-env/bin/activate
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