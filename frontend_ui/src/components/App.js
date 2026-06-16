import React, {useState, useEffect} from "react";
import { Link } from "react-router-dom";
import logo from '../assets/hopecoin-logo.svg';
import {API_BASE_URL} from '../config';


function App() {
  const [walletInfo, setWalletInfo] = useState({});
  const [error, setError] = useState('');
  const [blockchainLength, setBlockchainLength] = useState('-');
  const [pendingTransactions, setPendingTransactions] = useState([]);
  const [isMining, setIsMining] = useState(false);
  const [message, setMessage] = useState('');

  const fetchDashboard = () => {
    setError('');
    setMessage('');

    Promise.all([
      fetch(`${API_BASE_URL}/wallet/info`),
      fetch(`${API_BASE_URL}/blockchain/length`),
      fetch(`${API_BASE_URL}/transactions`)
    ])
      .then(responses => {
        responses.forEach(response => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }
        });

        return Promise.all(responses.map(response => response.json()));
      })
      .then(([walletJson, blockchainLengthJson, transactionsJson]) => {
        setWalletInfo(walletJson);
        setBlockchainLength(blockchainLengthJson);
        setPendingTransactions(transactionsJson);
      })
      .catch(() => {
        setError('No se pudo conectar con el backend. Ejecuta python3 -m backend.app en otra terminal.');
      });
  };

  const mineTransactions = () => {
    setIsMining(true);
    setMessage('');

    fetch(`${API_BASE_URL}/blockchain/mine`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
      })
      .then(() => {
        setMessage('Bloque minado y transacciones consolidadas.');
        fetchDashboard();
      })
      .catch(error => {
        setMessage(`No se pudo minar: ${error.message}`);
      })
      .finally(() => setIsMining(false));
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const {address, balance} = walletInfo;

  return (
    <div className="App dashboard-shell">
      <header className="dashboard-header">
        <div className="brand-lockup">
          <img className="logo" src={logo} alt="HopeCoin" />
          <div>
            <p className="eyebrow">Cripto-donaciones</p>
            <h1>HopeCoin</h1>
            <p className="slogan">La evolución digital del apoyo humano</p>
          </div>
        </div>
        <button className="ghost-button" type="button" onClick={fetchDashboard}>
          Actualizar
        </button>
      </header>

      {error && <div className="ErrorMessage">{error}</div>}
      {message && <div className="StatusMessage">{message}</div>}

      <section className="dashboard-grid">
        <article className="wallet-panel">
          <div className="panel-heading">
            <span>Billetera activa</span>
            <strong>{balance ?? '-'}</strong>
          </div>
          <p className="wallet-address">{address || 'Sin conexión con backend'}</p>
          <div className="metric-row">
            <div>
              <span>Bloques</span>
              <strong>{blockchainLength}</strong>
            </div>
            <div>
              <span>Pool</span>
              <strong>{pendingTransactions.length}</strong>
            </div>
          </div>
        </article>

        <article className="action-panel">
          <Link className="action-card" to="/blockchain">
            <span className="action-icon">▦</span>
            <strong>Ver blockchain</strong>
            <small>Explora bloques, hashes y transacciones minadas.</small>
          </Link>

          <Link className="action-card" to="/conduct-transaction">
            <span className="action-icon">◇</span>
            <strong>Realizar transacción</strong>
            <small>Selecciona una organización simulada y envía HopeCoins.</small>
          </Link>

          <button className="action-card action-button" type="button" onClick={mineTransactions} disabled={isMining}>
            <span className="action-icon">⬡</span>
            <strong>{isMining ? 'Minando...' : 'Minar transacciones'}</strong>
            <small>Consolida el pool en un nuevo bloque de la cadena.</small>
          </button>
        </article>
      </section>
    </div>
  );
}

export default App;
