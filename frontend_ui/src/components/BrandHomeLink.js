import React from 'react';
import { Link } from 'react-router-dom';
import logo from '../assets/hopecoin-logo.svg';

function BrandHomeLink() {
    return (
        <Link className="mini-brand" to="/" aria-label="Regresar al inicio de HopeCoin">
            <img src={logo} alt="HopeCoin" />
            <span>HopeCoin</span>
        </Link>
    );
}

export default BrandHomeLink;
