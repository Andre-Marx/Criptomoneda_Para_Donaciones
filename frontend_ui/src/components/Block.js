import React, {useState} from "react";
import {MILLISECONDS_PY} from '../config';
import Transaction from "./Transaction";

function shortenHash(value) {
    const stringValue = `${value || '-'}`;

    if (stringValue.length <= 24) {
        return stringValue;
    }

    return `${stringValue.slice(0, 12)}...${stringValue.slice(-10)}`;
}

function formatBlockData(value) {
    if (value === null || value === undefined || value === '') {
        return 'Sin datos adicionales.';
    }

    if (typeof value === 'string') {
        return value;
    }

    return JSON.stringify(value);
}

function Block({block, isLatest}) {
    const [isExpanded, setIsExpanded] = useState(false);
    const {timestamp, hash, difficulty, last_hash, nonce, number} = block;
    const data = Array.isArray(block.data) ? block.data : [];
    const hasRawData = !Array.isArray(block.data) && block.data;
    const timestampDisplay = new Date(timestamp / MILLISECONDS_PY).toLocaleString();
    const transactionLabel = data.length === 1 ? '1 transacción' : `${data.length} transacciones`;

    return (
        <article className={isExpanded ? 'chain-block is-expanded' : 'chain-block'}>
            <div className="chain-rail" aria-hidden="true">
                <span className="chain-node">{number}</span>
            </div>

            <div className="block-card">
                <button
                    className="block-summary"
                    type="button"
                    aria-expanded={isExpanded}
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    <span>
                        <span className="block-kicker">{isLatest ? 'Bloque más reciente' : 'Bloque encadenado'}</span>
                        <strong>Bloque #{number}</strong>
                        <small>Encabezado verificado con {transactionLabel}</small>
                    </span>
                    <span className="expand-indicator">{isExpanded ? 'Ocultar' : 'Ver detalle'}</span>
                </button>

                <div className="block-header-grid">
                    <div className="header-field">
                        <span>Hash</span>
                        <code title={hash}>{shortenHash(hash)}</code>
                    </div>
                    <div className="header-field">
                        <span>Hash anterior</span>
                        <code title={last_hash}>{shortenHash(last_hash)}</code>
                    </div>
                    <div className="header-field">
                        <span>Timestamp</span>
                        <strong>{timestampDisplay}</strong>
                    </div>
                    <div className="header-field">
                        <span>Dificultad</span>
                        <strong>{difficulty}</strong>
                    </div>
                    <div className="header-field">
                        <span>Nonce</span>
                        <strong>{nonce}</strong>
                    </div>
                    <div className="header-field">
                        <span>Transacciones</span>
                        <strong>{data.length}</strong>
                    </div>
                </div>

                {isExpanded && (
                    <div className="block-details">
                        <div className="detail-heading">
                            <span>Contenido del bloque</span>
                            <strong>{transactionLabel}</strong>
                        </div>

                        {data.length > 0 && data.map((transaction, index) => (
                            <div className="block-transaction" key={transaction.id || index}>
                                <Transaction transaction={transaction} />
                            </div>
                        ))}

                        {data.length === 0 && (
                            <p className="empty-state">
                                {hasRawData ? formatBlockData(block.data) : 'Este bloque no contiene transacciones.'}
                            </p>
                        )}
                    </div>
                )}
            </div>
        </article>
    );
}

export default Block;
