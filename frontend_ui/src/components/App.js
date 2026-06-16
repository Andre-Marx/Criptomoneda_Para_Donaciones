import React, {useState, useEffect} from "react";
import { useHistory } from 'react-router-dom';
import { Link } from "react-router-dom";
import logo from '../assets/hopecoin-logo.svg';
import {API_BASE_URL} from '../config';


function App() {
  const [walletInfo, setWalletInfo] = useState({});
  const [error, setError] = useState('');
  const [blockchainLength, setBlockchainLength] = useState('-');
  const [pendingTransactions, setPendingTransactions] = useState([]);
  const [message, setMessage] = useState('');
  const history = useHistory();

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

          <button className="action-card action-button" type="button" onClick={() => history.push('/transaction-pool')}>
            <span className="action-icon">⬡</span>
            <strong>Minar transacciones</strong>
            <small>
              {pendingTransactions.length > 0
                ? 'Revisa el mempool y consolida el bloque.'
                : 'Primero agrega una transacción al mempool.'}
            </small>
          </button>
        </article>
      </section>
    </div>
  );
}

export default App;
