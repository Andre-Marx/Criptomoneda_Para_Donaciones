import React, {useState, useEffect} from "react";
import { Link, useHistory } from 'react-router-dom'; 
import {FormGroup, FormControl, Button} from 'react-bootstrap';
import { API_BASE_URL } from "../config";



function ConductTransaction() {
    const [amount, setAmount] = useState(0);
    const [recipient, setRecipient] = useState('');
    const [knownAddresses, setKnownAddresses] = useState([]);
    const [message, setMessage] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const history = useHistory();

    // Array con la información de las organizaciones sin fines de lucro
    const nonprofitOrganizations = [
        { name: 'Estrellas Solidarias', area: 'Educación', mission: 'Iluminar el camino de la educación para niños desfavorecidos, brindándoles acceso a recursos educativos de calidad y oportunidades para un futuro brillante.', address_wallet: knownAddresses[0] },
        { name: 'Manos que Sanan', area: 'Salud', mission: 'Proporcionar atención médica y apoyo emocional a comunidades marginadas, promoviendo la salud integral y el bienestar.', address_wallet: knownAddresses[1]},
        { name: 'Planeta Verde', area: 'Medio Ambiente', mission: 'Preservar y restaurar la salud del planeta mediante la promoción de prácticas sostenibles, la conservación de la biodiversidad y la conciencia ambiental.', address_wallet: knownAddresses[2]},
        { name: 'Sonrisas para Todos', area: 'Salud Mental', mission: 'Abogar por la salud mental positiva, ofreciendo recursos y programas que fomenten el bienestar emocional y destigmatizando las enfermedades mentales.', address_wallet: knownAddresses[3]},
        { name: 'Arte Inclusivo', area: 'Cultura y Arte', mission: 'Facilitar el acceso a las artes para todas las comunidades, promoviendo la inclusión y la diversidad a través de programas artísticos y culturales.', address_wallet: knownAddresses[4]},
        { name: 'Hogar Esperanza', area: 'Vivienda', mission: 'Combatir la falta de vivienda proporcionando refugio, asistencia y recursos para ayudar a las personas a recuperar la estabilidad en sus vidas.', address_wallet: knownAddresses[5]},
        { name: 'Alas de Solidaridad', area: 'Desarrollo Comunitario', mission: 'Empoderar a comunidades marginadas mediante la implementación de proyectos de desarrollo sostenible que promuevan la autosuficiencia y la igualdad.', address_wallet: knownAddresses[6]},
        { name: 'Sabores del Cambio', area: 'Seguridad Alimentaria', mission: 'Luchar contra la hambruna y la malnutrición, brindando acceso a alimentos nutritivos y educación sobre prácticas agrícolas sostenibles.', address_wallet: knownAddresses[7]},
        { name: 'Notas de Esperanza', area: 'Educación Musical', mission: 'Facilitar el acceso a la educación musical para niños y jóvenes, fomentando la expresión creativa y el desarrollo de habilidades a través de la música.', address_wallet: knownAddresses[8]},
        { name: 'Construyendo Puentes', area: 'Derechos Humanos', mission: 'Defender y promover los derechos humanos, construyendo puentes de comprensión y tolerancia a través de la educación, la sensibilización y la promoción de la justicia social.', address_wallet: knownAddresses[9]},
        // ... (Repite para las otras organizaciones)
    ];

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
                Usar dirección
            </Button>
        </div>
    );

    useEffect(() => {
        fetch(`${API_BASE_URL}/known-addresses`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return response.json();
            })
            .then(json => setKnownAddresses(json))
            .catch(() => setMessage('No se pudieron cargar las direcciones conocidas. Revisa que el backend esté activo.'));
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
            alert(`¡Éxito!\nSe transfirieron ${amount} hopecoins que equivalen a ${Math.round((amount*12.7) * 10 ) / 10} pesos`);
            history.push('/transaction-pool');
        })
        .catch(error => {
            setMessage(`No se pudo realizar la transacción: ${error.message}`);
        })
        .finally(() => setIsSubmitting(false));
    }
    
    return (
        <div className = "ConductTransaction">
            <Link to='/'>Inicio</Link>
            <hr />
            <h3>Realizar Transacción</h3>
            <br />
            <FormGroup>
                <FormControl type="text" placeholder="Dirección destino" value={recipient} onChange={updateRecipient} />
            </FormGroup>
            <br/>
            <FormGroup>
                <FormControl type="number" min="1" placeholder="Monto" value={amount} onChange={updateAmount} />
            </FormGroup>
            <br/>
            <div>
                <Button variant="danger" onClick={submitTransaction} disabled={isSubmitting}>
                    {isSubmitting ? 'Enviando...' : 'Enviar'}
                </Button>
            </div>
            {message && <div className="ErrorMessage">{message}</div>}
            <br />
            <br />
            <hr />
            <h2>Direcciones Conocidas</h2>
            <div className="organization-grid">
                {nonprofitOrganizations.map((organization, index) => (
                <OrganizationCard key={index} {...organization} />) ) }
            </div>

        </div>
    )
}

export default ConductTransaction;
