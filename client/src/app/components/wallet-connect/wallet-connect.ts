import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { TransactionService } from '../../services/transaction';

@Component({
  selector: 'app-wallet-connect',
  templateUrl: './wallet-connect.html',
  styleUrls: ['./wallet-connect.css'],
  imports: [FormsModule, CommonModule],
})

export class WalletConnectComponent {
  txService = inject(TransactionService);

  wifInput = signal('');
  loading = signal(false);
  error = signal('');

  connect(): void {
    if (!this.wifInput().trim()) return;
    this.loading.set(true);
    this.error.set('');

    this.txService.connectWallet(this.wifInput().trim()).subscribe({
      next: () => {
        this.loading.set(false);
        this.wifInput.set('');
      },
      error: (err) => {
        this.error.set(err.error?.error ?? 'Could not connect wallet.');
        this.loading.set(false);
      },
    });
  }
}