import React, {useState, useEffect, useCallback} from 'react';
import { Link } from 'react-router-dom'; 
import {Button} from 'react-bootstrap';
import {API_BASE_URL} from '../config';
import Block from './Block';

const PAGE_RANGE = 3;

function Blockchain() {
    const [blockchain, setBlockchain] = useState([]);
    const [blockchainLength, setBlockchainLength] = useState(0);
    const [message, setMessage] = useState('');

    const fetchBlockchainPage = useCallback(({start, end}) => {
        setMessage('');

        fetch(`${API_BASE_URL}/blockchain/range?start=${start}&end=${end}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return response.json();
            })
            .then(json => setBlockchain(json))
            .catch(error => {
                setMessage(`No se pudo cargar la blockchain: ${error.message}`);
            });
    }, []);

    const fetchBlockchainLength = useCallback(() => {
        setMessage('');

        fetch(`${API_BASE_URL}/blockchain/length`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return response.json();
            })
            .then(json => setBlockchainLength(json))
            .catch(error => {
                setMessage(`No se pudo cargar la longitud de la blockchain: ${error.message}`);
            });
    }, []);

    const refreshBlockchain = useCallback(() => {
        fetchBlockchainPage({start:0, end: PAGE_RANGE});
        fetchBlockchainLength();
    }, [fetchBlockchainPage, fetchBlockchainLength]);

    useEffect(() => {
        refreshBlockchain();
    }, [refreshBlockchain]);

    const buttonNumbers = [];
    for (let i=0; i<blockchainLength/PAGE_RANGE; i++) {
        buttonNumbers.push(i);
    }

    return (
        <div className="Blockchain">
            <Link to='/'>Inicio</Link>
            <hr />
            <h3>Blockchain</h3>
            {message && <div className="ErrorMessage">{message}</div>}
            <Button size="sm" variant="danger" onClick={refreshBlockchain}>
                Actualizar
            </Button>
            <div>
                {
                blockchain.map(block => <Block key={block.hash} block={block} />)
                }
            </div>
            <div>
                {
                    buttonNumbers.map(number => {
                        const start = number * PAGE_RANGE;
                        const end = (number+1) * PAGE_RANGE;

                        return (
                            <span key={number} onClick={() => fetchBlockchainPage({start, end})}>
                                <Button size="sm" variant="danger">
                                    {number+1}
                                </Button>{' '}

                            </span>
                        )
                    })
                }
            </div>
        </div>
    )
}

export default Blockchain;
