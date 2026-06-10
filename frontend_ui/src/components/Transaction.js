import React from "react";

function Transaction({transaction}) {
    const {input, output} = transaction;
    const recipients = Object.keys(output);
    console.log(typeof input.signature)

    return (
        <div className="Transaction">
            <div>De: {input.address}</div>
            <div>Firma del Emisor: {input.signature}</div>
            <div>Para: {output.recipients_address}</div>
            <div>Monto Recibido: {output.amount_received}</div>
            <div>Llave Pública del Receptor: {output.recipients_public_key}</div>
            <div>Firma del Receptor: {output.recipients_signature}</div>
            <div>Balance del Emisor: {output.sender_balance}</div>

           
        </div>
    )
}

export default Transaction;