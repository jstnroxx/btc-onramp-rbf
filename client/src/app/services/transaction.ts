import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { WalletInfo, Transaction } from '../interfaces/transaction.model';

@Injectable({ providedIn: 'root' })
export class TransactionService {
  private readonly API = 'http://localhost:8000/api';

  // Signals for wallet state
  private wifKey = signal<string | null>(null);
  private walletInfo = signal<WalletInfo | null>(null);

  // Public read-only signals
  readonly wallet = computed(() => this.walletInfo());
  readonly isWalletConnected = computed(() => this.wifKey() !== null);

  constructor(private http: HttpClient) {}

  // ── Wallet ──────────────────────────────────────────────────────────────────

  connectWallet(wifKey: string): Observable<WalletInfo> {
    return this.http
      .post<WalletInfo>(`${this.API}/wallet/info/`, { wifKey: wifKey })
      .pipe(
        tap((info) => {
          this.wifKey.set(wifKey);
          this.walletInfo.set(info);
        })
      );
  }

  disconnectWallet(): void {
    this.wifKey.set(null);
    this.walletInfo.set(null);
  }

  // ── Fees ────────────────────────────────────────────────────────────────────

  getRecommendedFee(): Observable<{ feeSatPerVB: number }> {
    return this.http.get<{ feeSatPerVB: number }>(`${this.API}/fees/recommended/`);
  }

  // ── Transactions ────────────────────────────────────────────────────────────

  getTransactions(): Observable<Transaction[]> {
    return this.http.get<Transaction[]>(`${this.API}/transactions/`);
  }

  sendTransaction(recipient: string, amountSat: number, feeSatPerVb: number): Observable<Transaction> {
    return this.http.post<Transaction>(`${this.API}/transactions/`, {
      wifKey: this.wifKey(),
      recipient,
      amountSat: amountSat,
      feeSatPerVB: feeSatPerVb,
    });
  }

  bumpFee(txId: number, newFeeSatPerVb: number): Observable<{ original: Transaction; replacement: Transaction }> {
    return this.http.post<{ original: Transaction; replacement: Transaction }>(
      `${this.API}/transactions/${txId}/rbf/`,
      { wifKey: this.wifKey(), newFeeSatPerVB: newFeeSatPerVb }
    );
  }
}