import React, {useState, useEffect} from "react";
import { Link, useHistory } from 'react-router-dom'; 
import {FormGroup, FormControl, Button} from 'react-bootstrap';
import { API_BASE_URL } from "../config";



function ConductTransaction() {
    const [amount, setAmount] = useState(0);
    const [recipient, setRecipient] = useState('');
    const [nonprofitOrganizations, setNonprofitOrganizations] = useState([]);
    const [message, setMessage] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const history = useHistory();

    const selectedOrganization = nonprofitOrganizations.find(
        organization => organization.address_wallet === recipient
    );

    // Componente funcional que representa una tarjeta de organización
    const OrganizationCard = ({ name, area, mission, address_wallet }) => (
        <div className="organization-card">
            <br/>
            <h3>{name}</h3>
            <p><strong><b>Área de Apoyo</b>:</strong> {area}</p>
            <p><strong>Misión:</strong> {mission}</p>
            <p><strong>Dirección:</strong> {address_wallet || 'No disponible todavía'}</p>
            <Button
                disabled={!address_wallet}
                size="sm"
                variant="danger"
                onClick={() => setRecipient(address_wallet)}
            >
                Seleccionar
            </Button>
        </div>
    );

    useEffect(() => {
        fetch(`${API_BASE_URL}/nonprofit-organizations`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return response.json();
            })
            .then(json => setNonprofitOrganizations(json))
            .catch(() => setMessage('No se pudieron cargar las organizaciones. Revisa que el backend esté activo.'));
    }, []);

    const updateRecipient = event => {
        setRecipient(event.target.value);
    }

    const updateAmount = event => {
        setAmount(Number(event.target.value));
    }

    const submitTransaction = () => {
        if (!recipient || amount <= 0) {
            setMessage('Captura una dirección destino y un monto mayor a cero.');
            return;
        }

        setIsSubmitting(true);
        setMessage('');

        fetch(`${API_BASE_URL}/wallet/transact`, {
            method: 'POST', 
            headers: {'Content-Type':'application/json'}, 
            body: JSON.stringify({recipient, amount})
        }).then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return response.json();
        })
        .then(json => {
            console.log('submitTransaction json', json);
            alert(`¡Éxito!\nSe transfirieron ${amount} CriptoCoins que equivalen a ${Math.round((amount*12.7) * 10 ) / 10} pesos`);
            history.push('/transaction-pool');
        })
        .catch(error => {
            setMessage(`No se pudo realizar la transacción: ${error.message}`);
        })
        .finally(() => setIsSubmitting(false));
    }
    
    return (
        <div className = "ConductTransaction">
            <Link className="back-link" to='/'>Inicio</Link>
            <section className="page-header">
                <p className="eyebrow">CriptoCoin</p>
                <h2>Realizar transacción</h2>
                <p>Elige una organización simulada y envía apoyo digital desde tu billetera.</p>
            </section>

            <FormGroup>
                <FormControl as="select" value={recipient} onChange={updateRecipient}>
                    <option value="">Selecciona una organización</option>
                    {
                        nonprofitOrganizations.map(organization => (
                            <option key={organization.address_wallet} value={organization.address_wallet}>
                                {organization.name} · {organization.area}
                            </option>
                        ))
                    }
                </FormControl>
            </FormGroup>

            {selectedOrganization && (
                <div className="selection-summary">
                    <span>Destino seleccionado</span>
                    <strong>{selectedOrganization.name}</strong>
                    <p>{selectedOrganization.address_wallet}</p>
                </div>
            )}

            <FormGroup>
                <FormControl type="number" min="1" placeholder="Monto" value={amount} onChange={updateAmount} />
            </FormGroup>

            <div>
                <Button variant="danger" onClick={submitTransaction} disabled={isSubmitting}>
                    {isSubmitting ? 'Enviando...' : 'Enviar'}
                </Button>
            </div>
            {message && <div className="ErrorMessage">{message}</div>}

            <h2>Organizaciones sin fines de lucro</h2>
            <div className="organization-grid">
                {nonprofitOrganizations.map((organization, index) => (
                <OrganizationCard key={organization.address_wallet || index} {...organization} />) ) }
            </div>

        </div>
    )
}

export default ConductTransaction;
