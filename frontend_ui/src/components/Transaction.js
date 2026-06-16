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

function SignatureField({label, value}) {
    return (
        <div className="signature-field">
            <strong>{label}</strong>
            <code>{formatValue(value)}</code>
        </div>
    );
}

function Transaction({transaction}) {
    const {input, output, signatures = {}} = transaction;
    const outputEntries = Object.entries(output);
    const senderSignature = signatures.sender?.signature || input.signature;
    const recipientSignature = signatures.recipient?.signature;
    const recipientAddress = signatures.recipient?.address;

    return (
        <div className="Transaction">
            <div>De: {input.address}</div>
            {recipientAddress && <div>Para: {recipientAddress}</div>}
            <div>Monto de Entrada: {formatValue(input.amount)}</div>

            <div className="signature-grid">
                <SignatureField label="Firma del emisor" value={senderSignature} />
                <SignatureField label="Firma del receptor" value={recipientSignature} />
            </div>

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
