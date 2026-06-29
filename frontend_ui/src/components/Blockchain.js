import React, {useState, useEffect, useCallback} from 'react';
import {API_BASE_URL, SECONDS_JS} from '../config';
import Block from './Block';
import BrandHomeLink from './BrandHomeLink';

const PAGE_RANGE = 3;
const POLL_INTERVAL = 2 * SECONDS_JS;

function Blockchain() {
    const [blockchain, setBlockchain] = useState([]);
    const [blockchainLength, setBlockchainLength] = useState(0);
    const [message, setMessage] = useState('');
    const [currentPage, setCurrentPage] = useState(0);

    const fetchBlockchainPage = useCallback(({start, end, page = 0}) => {
        setMessage('');

        fetch(`${API_BASE_URL}/blockchain/range?start=${start}&end=${end}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return response.json();
            })
            .then(json => {
                setBlockchain(json);
                setCurrentPage(page);
            })
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
        const start = currentPage * PAGE_RANGE;
        const end = (currentPage + 1) * PAGE_RANGE;

        fetchBlockchainPage({start, end, page: currentPage});
        fetchBlockchainLength();
    }, [currentPage, fetchBlockchainPage, fetchBlockchainLength]);

    useEffect(() => {
        refreshBlockchain();

        const intervalId = setInterval(refreshBlockchain, POLL_INTERVAL);

        return () => clearInterval(intervalId);
    }, [refreshBlockchain]);

    const pageCount = Math.ceil(blockchainLength / PAGE_RANGE);
    const buttonNumbers = Array.from({length: pageCount}, (_, index) => index);
    const visibleStart = blockchainLength === 0 ? 0 : currentPage * PAGE_RANGE + 1;
    const visibleEnd = Math.min((currentPage + 1) * PAGE_RANGE, blockchainLength);

    return (
        <div className="Blockchain">
            <BrandHomeLink />

            <section className="page-header blockchain-page-header">
                <div>
                    <p className="eyebrow">Ledger HopeCoin</p>
                    <h2>Ver blockchain</h2>
                    <p>Bloques minados, hashes enlazados y transacciones registradas.</p>
                </div>
                <button className="ghost-button" type="button" onClick={refreshBlockchain}>
                    Actualizar
                </button>
            </section>

            {message && <div className="ErrorMessage">{message}</div>}

            <section className="chain-overview">
                <div>
                    <span>Longitud total</span>
                    <strong>{blockchainLength}</strong>
                </div>
                <div>
                    <span>Vista actual</span>
                    <strong>{visibleStart}-{visibleEnd}</strong>
                </div>
                <div>
                    <span>Orden</span>
                    <strong>Reciente primero</strong>
                </div>
            </section>

            <section className="blockchain-timeline">
                {
                    blockchain.length > 0
                        ? blockchain.map((block, index) => (
                            <Block
                                key={block.hash}
                                block={block}
                                isLatest={currentPage === 0 && index === 0}
                            />
                        ))
                        : <div className="empty-state">No hay bloques para mostrar.</div>
                }
            </section>

            {buttonNumbers.length > 1 && (
                <nav className="pagination-bar" aria-label="Páginas de la blockchain">
                    {
                        buttonNumbers.map(number => {
                            const start = number * PAGE_RANGE;
                            const end = (number + 1) * PAGE_RANGE;

                            return (
                                <button
                                    className={number === currentPage ? 'pagination-button is-active' : 'pagination-button'}
                                    key={number}
                                    type="button"
                                    onClick={() => fetchBlockchainPage({start, end, page: number})}
                                >
                                    {number + 1}
                                </button>
                            );
                        })
                    }
                </nav>
            )}
        </div>
    );
}

export default Blockchain;
