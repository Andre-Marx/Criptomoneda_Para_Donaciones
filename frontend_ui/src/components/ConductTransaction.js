import React, {useState, useEffect} from "react";
import { useHistory } from 'react-router-dom'; 
import {FormGroup, FormControl, Button} from 'react-bootstrap';
import { API_BASE_URL } from "../config";
import BrandHomeLink from './BrandHomeLink';



function ConductTransaction() {
    const [amount, setAmount] = useState(0);
    const [recipient, setRecipient] = useState('');
    const [nonprofitOrganizations, setNonprofitOrganizations] = useState([]);
    const [walletInfo, setWalletInfo] = useState({});
    const [message, setMessage] = useState('');
    const [messageType, setMessageType] = useState('status');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const history = useHistory();
    const availableBalance = walletInfo.pending_balance ?? walletInfo.balance ?? 0;
    const pendingSpend = walletInfo.pending_spend ?? 0;

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

    const fetchWalletInfo = () => {
        return fetch(`${API_BASE_URL}/wallet/info`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return response.json();
            })
            .then(json => setWalletInfo(json));
    }

    useEffect(() => {
        fetch(`${API_BASE_URL}/nonprofit-organizations`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return response.json();
            })
            .then(json => setNonprofitOrganizations(json))
            .catch(() => {
                setMessageType('error');
                setMessage('No se pudieron cargar las organizaciones. Revisa que el backend esté activo.');
            });

        fetchWalletInfo()
            .catch(() => {
                setMessageType('error');
                setMessage('No se pudo cargar el saldo de la billetera. Revisa que el backend esté activo.');
            });
    }, []);

    const updateRecipient = event => {
        setRecipient(event.target.value);
    }

    const updateAmount = event => {
        setAmount(Number(event.target.value));
    }

    const submitTransaction = () => {
        if (!recipient || amount <= 0) {
            setMessageType('error');
            setMessage('Captura una dirección destino y un monto mayor a cero.');
            return;
        }

        if (amount > availableBalance) {
            setMessageType('error');
            setMessage(`Saldo disponible insuficiente. Puedes enviar hasta ${availableBalance} HopeCoins antes de minar.`);
            return;
        }

        setIsSubmitting(true);
        setMessageType('status');
        setMessage('');

        fetch(`${API_BASE_URL}/wallet/transact`, {
            method: 'POST', 
            headers: {'Content-Type':'application/json'}, 
            body: JSON.stringify({recipient, amount})
        }).then(response => {
            return response.json().then(json => {
                if (!response.ok) {
                    throw new Error(json.message || `HTTP ${response.status}`);
                }

                return json;
            });
        })
        .then(json => {
            console.log('submitTransaction json', json);
            alert(`¡Éxito!\nSe transfirieron ${amount} HopeCoins que equivalen a ${Math.round((amount*12.7) * 10 ) / 10} pesos`);
            return fetchWalletInfo();
        })
        .then(() => {
            const wantsAnotherTransaction = window.confirm('La transacción quedó en el mempool. ¿Deseas realizar otra transacción?');

            if (wantsAnotherTransaction) {
                setRecipient('');
                setAmount(0);
                setMessageType('status');
                setMessage('Puedes agregar otra transacción antes de minar el bloque.');
            } else {
                history.push('/transaction-pool');
            }
        })
        .catch(error => {
            setMessageType('error');
            setMessage(`No se pudo realizar la transacción: ${error.message}`);
        })
        .finally(() => setIsSubmitting(false));
    }
    
    return (
        <div className = "ConductTransaction">
            <BrandHomeLink />
            <section className="page-header">
                <p className="eyebrow">HopeCoin</p>
                <h2>Realizar transacción</h2>
                <p>Elige una organización simulada y envía apoyo digital desde tu billetera.</p>
            </section>

            <section className="transaction-balance-strip">
                <div>
                    <span>Balance total</span>
                    <strong>{walletInfo.balance ?? '-'}</strong>
                </div>
                <div>
                    <span>Reservado en mempool</span>
                    <strong>{pendingSpend}</strong>
                </div>
                <div>
                    <span>Disponible</span>
                    <strong>{availableBalance}</strong>
                </div>
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
                <FormControl type="number" min="1" max={availableBalance} placeholder="Monto" value={amount} onChange={updateAmount} />
            </FormGroup>

            <div>
                <Button variant="danger" onClick={submitTransaction} disabled={isSubmitting || availableBalance <= 0}>
                    {isSubmitting ? 'Enviando...' : 'Enviar'}
                </Button>
            </div>
            {message && (
                <div className={messageType === 'error' ? 'ErrorMessage' : 'StatusMessage'}>
                    {message}
                </div>
            )}

            <h2>Organizaciones sin fines de lucro</h2>
            <div className="organization-grid">
                {nonprofitOrganizations.map((organization, index) => (
                <OrganizationCard key={organization.address_wallet || index} {...organization} />) ) }
            </div>

        </div>
    )
}

export default ConductTransaction;
