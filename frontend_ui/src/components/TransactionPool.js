import React, {useState, useEffect, useCallback} from "react";
import {Link} from 'react-router-dom';
import { Button } from "react-bootstrap";
import Transaction from './Transaction';
import { API_BASE_URL, SECONDS_JS} from "../config";
import BrandHomeLink from './BrandHomeLink';

const POLL_INTERVAL = 1 * SECONDS_JS;
const MINING_POLL_INTERVAL = 1 * SECONDS_JS;

function shortenHash(value) {
    const stringValue = `${value || '-'}`;

    if (stringValue.length <= 28) {
        return stringValue;
    }

    return `${stringValue.slice(0, 16)}...${stringValue.slice(-10)}`;
}

function TransactionPool() {
    const [transactions, setTransactions] = useState([]);
    const [message, setMessage] = useState('');
    const [isMining, setIsMining] = useState(false);
    const [miningStatus, setMiningStatus] = useState({});
    const [networkStatus, setNetworkStatus] = useState({});

    const fetchTransactions = useCallback(() => {
        setMessage('');

        fetch(`${API_BASE_URL}/transactions`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return response.json();
            })
            .then(json => setTransactions(json))
            .catch(error => {
                setMessage(`No se pudo cargar el pool de transacciones: ${error.message}`);
            });
    }, []);

    const fetchMiningStatus = useCallback(() => {
        fetch(`${API_BASE_URL}/mining/status`)
            .then(response => response.ok ? response.json() : null)
            .then(json => {
                if (!json) {
                    return;
                }

                setMiningStatus(json);
                setIsMining(Boolean(json.is_mining));

                if (['won', 'won_by_peer', 'stopped'].includes(json.status)) {
                    fetchTransactions();
                }
            })
            .catch(() => {});
    }, [fetchTransactions]);

    const fetchNetworkStatus = useCallback(() => {
        fetch(`${API_BASE_URL}/network/status`)
            .then(response => response.ok ? response.json() : null)
            .then(json => {
                if (json) {
                    setNetworkStatus(json);
                }
            })
            .catch(() => {});
    }, []);

    useEffect(() => {
        fetchTransactions();
        fetchMiningStatus();
        fetchNetworkStatus();

        const transactionIntervalId = setInterval(fetchTransactions, POLL_INTERVAL);
        const miningIntervalId = setInterval(fetchMiningStatus, MINING_POLL_INTERVAL);
        const networkIntervalId = setInterval(fetchNetworkStatus, MINING_POLL_INTERVAL);

        return () => {
            clearInterval(transactionIntervalId);
            clearInterval(miningIntervalId);
            clearInterval(networkIntervalId);
        };
    }, [fetchTransactions, fetchMiningStatus, fetchNetworkStatus]);

    const fetchMineBlock = () => {
        setIsMining(true);
        setMessage('');

        fetch(`${API_BASE_URL}/blockchain/mine`)
            .then(response => {
                return response.json().then(json => {
                    if (!response.ok && response.status !== 409) {
                        throw new Error(json.message || `HTTP ${response.status}`);
                    }

                    return json;
                });
            })
            .then(json => {
                setMiningStatus(json);
                setMessage('Competencia de minado iniciada. Observa cómo cambian el nonce y el hash.');
            })
            .catch(error => {
                setMessage(`No se pudo minar el bloque: ${error.message}`);
            })
            .finally(() => fetchMiningStatus());
    }

    const activeMiners = Object.values(miningStatus.active_miners || {});
    const winnerText = miningStatus.winner
        ? `${miningStatus.winner}${miningStatus.winner_address ? ` (${shortenHash(miningStatus.winner_address)})` : ''}`
        : 'Sin ganador todavía';

    return (
        <div className="TransactionPool">
            <BrandHomeLink />
            <section className="page-header">
                <p className="eyebrow">HopeCoin</p>
                <h2>Grupo de transacciones</h2>
                <p>Transacciones pendientes antes de consolidarse en el siguiente bloque.</p>
            </section>

            <section className="network-mining-panel">
                <div className="network-card">
                    <span>Nodo local</span>
                    <strong>{networkStatus.node_id || miningStatus.node_id || '-'}</strong>
                    <small>{networkStatus.mode || 'server'} · {networkStatus.peer_count || 0} peers conectados</small>
                    {networkStatus.lan_ip && <code>{networkStatus.lan_ip}:{networkStatus.api_port}</code>}
                </div>
                <div className="network-card">
                    <span>Prueba de trabajo</span>
                    <strong>{miningStatus.status || 'idle'}</strong>
                    <small>Dificultad {miningStatus.difficulty || '-'}</small>
                    <code>nonce {miningStatus.nonce || 0}</code>
                </div>
                <div className="network-card">
                    <span>Hash actual</span>
                    <strong>{shortenHash(miningStatus.hash)}</strong>
                    <small>{miningStatus.message || 'Esperando mineros.'}</small>
                </div>
                <div className="network-card">
                    <span>Ganador</span>
                    <strong>{winnerText}</strong>
                    <small>Recompensa: {miningStatus.reward || 50} HopeCoins</small>
                </div>
            </section>

            {activeMiners.length > 0 && (
                <section className="miners-strip">
                    {activeMiners.map(miner => (
                        <div key={miner.node_id}>
                            <span>{miner.node_id}</span>
                            <strong>{miner.status}</strong>
                            <code>nonce {miner.nonce || 0} · {shortenHash(miner.hash)}</code>
                        </div>
                    ))}
                </section>
            )}

            {message && <div className="StatusMessage">{message}</div>}
            <div className="transaction-list">
                {
                    transactions.map(transaction => (
                        <div className="transaction-list-item" key={transaction.id}>
                            <Transaction transaction={transaction} />
                        </div>
                    ))
                }
                {transactions.length === 0 && (
                    <div className="empty-state">No hay transacciones pendientes.</div>
                )}
            </div>
            <div className="pool-actions">
                <Button
                    variant="danger"
                    onClick={fetchMineBlock}
                    disabled={isMining || transactions.length === 0}
                >
                    {transactions.length === 0
                        ? 'Agrega transacciones para minar'
                        : isMining ? 'Minando...' : 'Competir para minar'}
                </Button>
                <Link className="ghost-button" to="/blockchain">
                    Ver blockchain
                </Link>
            </div>
        </div>
    )
}

export default TransactionPool;
