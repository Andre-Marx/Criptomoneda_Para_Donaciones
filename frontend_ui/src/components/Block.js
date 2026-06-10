import React, {useState} from "react";
import {Button} from 'react-bootstrap';
import {MILLISECONDS_PY} from '../config';
import Transaction from "./Transaction";

function ToggleTransactionDisplay({block}) {
    const [displayTransaction, setDisplayTransaction] = useState(false);
    const {data} = block;

    const toggleDisplayTransaction = () => {
        setDisplayTransaction(!displayTransaction);
    }

    if (displayTransaction) {
        return (
        <div>
            {
                data.map(transaction => (
                    <div key={transaction.id}>
                        <hr />
                        <Transaction transaction={transaction} />
                    </div>
                ))
            }
            <br />
            <Button variant="danger" size="sm" onClick={toggleDisplayTransaction}>Ver Menos</Button>
        </div>
        )
    }

    return (
        <div>
            <br />
            <Button variant = "danger" size = "sm" onClick = {toggleDisplayTransaction}>
                Ver Más
            </Button>
        </div>
    )
}

function Block({block}) {
    const {timestamp, hash, difficulty, last_hash, nonce, number, data} = block;
    const hashDisplay = `${hash}`;
    const timestampDisplay = new Date(timestamp / MILLISECONDS_PY).toLocaleString();

    return (
        <div className="Block">
            <div>Hash: {hashDisplay}</div>
            <div>Timestamp: {timestampDisplay}</div>
            <div>Dificultad: {difficulty}</div>
            <div>Nonce: {nonce}</div>
            <div>Número de Bloque: {number}</div>
            <div>Anterior Hash: {last_hash}</div>
            <ToggleTransactionDisplay block={block} />
        </div>
    )
}

export default Block;