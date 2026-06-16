import React, {useState, useEffect} from "react";
import {useHistory} from 'react-router-dom';
import { Button } from "react-bootstrap";
import Transaction from './Transaction';
import { API_BASE_URL, SECONDS_JS} from "../config";
import BrandHomeLink from './BrandHomeLink';

const POLL_INTERVAL = 10 * SECONDS_JS;

function TransactionPool() {
    const [transactions, setTransactions] = useState([]);
    const [message, setMessage] = useState('');
    const [isMining, setIsMining] = useState(false);
    const history = useHistory();

    const fetchTransactions = () => {
        setMessage('');

        fetch(`${API_BASE_URL}/transactions`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return response.json();
            })
            .then(json => {
                console.log('transactions json', json);

                setTransactions(json);
            })
            .catch(error => {
                setMessage(`No se pudo cargar el pool de transacciones: ${error.message}`);
            });
    }

    useEffect(() => {
        fetchTransactions();

        const intervalId = setInterval(fetchTransactions, POLL_INTERVAL);

        return () => clearInterval(intervalId);
    }, []);

    const fetchMineBlock = () => {
        setIsMining(true);
        setMessage('');

        fetch(`${API_BASE_URL}/blockchain/mine`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                alert('¡Éxito!');
                history.push('/blockchain');
            })
            .catch(error => {
                setMessage(`No se pudo minar el bloque: ${error.message}`);
            })
            .finally(() => setIsMining(false));
    }

    return (
        <div className="TransactionPool">
            <BrandHomeLink />
            <section className="page-header">
                <p className="eyebrow">HopeCoin</p>
                <h2>Grupo de transacciones</h2>
                <p>Transacciones pendientes antes de consolidarse en el siguiente bloque.</p>
            </section>
            {message && <div className="ErrorMessage">{message}</div>}
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
            <Button
                variant="danger"
                onClick={fetchMineBlock}
                disabled={isMining}
            >
                {isMining ? 'Minando...' : 'Mina un bloque con estas transacciones'}
            </Button>
        </div>
    )

}

export default TransactionPool;
