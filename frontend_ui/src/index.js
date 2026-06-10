import React from 'react';
// import ReactDOM from 'react-dom';
import { createRoot } from 'react-dom/client';
import {Router, Switch, Route} from 'react-router-dom';
import history from './history';
import './index.css';
import App from './components/App';
import Blockchain from './components/Blockchain';
import ConductTransaction from './components/ConductTransaction';
import TransactionPool from './components/TransactionPool';

// ReactDOM.render(
//   <Router history={createBrowserHistory()}>
//     <Switch>
//       <Route path='/' exact component={App} />
//       <Route path='/blockchain' component={Blockchain} />
//       <Route path='/conduct-transaction' component={ConductTransaction} />
//       <Route path='/transaction-pool' component={TransactionPool} />
//     </Switch>
//   </Router>,
//   document.getElementById('root')
// );

// const root = ReactDOM.createRoot(document.getElementById('root'));
const root = createRoot(document.getElementById('root'));
root.render(
  <Router history={history}>
    <Switch>
      <Route path='/' exact component={App} />
      <Route path='/blockchain' component={Blockchain} />
      <Route path='/conduct-transaction' component={ConductTransaction} />
      <Route path='/transaction-pool' component={TransactionPool} />
    </Switch>
  </Router>
);

