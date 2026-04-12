import { Component, viewChild } from '@angular/core';
import { WalletConnectComponent } from './components/wallet-connect/wallet-connect';
import { SendFormComponent } from './components/send-form/send-form';
import { TxListComponent } from './components/tx-list/tx-list';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  imports: [WalletConnectComponent, SendFormComponent, TxListComponent],
})
export class App {
  txList = viewChild.required(TxListComponent);
}