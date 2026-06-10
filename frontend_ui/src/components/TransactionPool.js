import React, {useState, useEffect} from "react";
import {Link, useHistory} from 'react-router-dom';
import { Button } from "react-bootstrap";
import Transaction from './Transaction';
import { API_BASE_URL, SECONDS_JS} from "../config";

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
            <Link to="/">Inicio</Link>
            <hr />
            <h3>Grupo de Transacciones</h3>
            {message && <div className="ErrorMessage">{message}</div>}
            <div>
                {
                    transactions.map(transaction => (
                        <div key={transaction.id}>
                            <hr />
                            <Transaction transaction={transaction} />
                        </div>
                    ))
                }
            </div>
            <hr />
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
