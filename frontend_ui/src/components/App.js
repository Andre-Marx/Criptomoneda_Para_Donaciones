import React, {useState, useEffect} from "react";
import { Link } from "react-router-dom";
import logo from '../assets/logo.png';
import {API_BASE_URL} from '../config';


function App() {
  const [walletInfo, setWalletInfo] = useState({});
  const [error, setError] = useState('');

  const fetchWalletInfo = () => {
    setError('');

    fetch(`${API_BASE_URL}/wallet/info`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
      })
      .then(json => setWalletInfo(json))
      .catch(() => {
        setError('No se pudo conectar con el backend. Ejecuta python3 -m backend.app en otra terminal.');
      });
  };

  useEffect(() => {
    fetchWalletInfo();
  }, []);

  const {address, balance} = walletInfo;

  return (
    <div className="App"> 
      <img className="logo" src={logo} alt="application-logo"/>
      <h3>Bienvenido a HopeCoin</h3>
      <br />
      <Link to="/blockchain">Blockchain</Link>
      <Link to="/conduct-transaction">Realizar Transacción</Link>
      <Link to="/transaction-pool">Grupo de Transacciones</Link>
      <br />
      <div className="WalletInfo">
        {error && <div className="ErrorMessage">{error}</div>}
        <div>Dirección de Billetera: {address}</div>
        <div>Balance: {balance}</div>
        <button type="button" onClick={fetchWalletInfo}>Actualizar</button>
      </div>
    </div>
  );
}

export default App;
