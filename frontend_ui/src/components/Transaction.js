import React from "react";

function formatValue(value) {
    if (Array.isArray(value)) {
        return value.join(', ');
    }

    if (value && typeof value === 'object') {
        return JSON.stringify(value);
    }

    return value || '-';
}

function Transaction({transaction}) {
    const {input, output} = transaction;
    const outputEntries = Object.entries(output);

    return (
        <div className="Transaction">
            <div>De: {input.address}</div>
            <div>Monto de Entrada: {formatValue(input.amount)}</div>
            <div>Firma del Emisor: {formatValue(input.signature)}</div>
            <div className="TransactionOutput">
                <strong>Salidas:</strong>
                {
                    outputEntries.map(([recipient, amount]) => (
                        <div key={recipient}>
                            <span>{recipient}</span>: <span>{formatValue(amount)}</span>
                        </div>
                    ))
                }
            </div>
        </div>
    )
}

export default Transaction;
