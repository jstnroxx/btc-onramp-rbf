import { Component, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { interval, Subscription, switchMap, startWith } from 'rxjs';
import { TransactionService } from '../../services/transaction';
import { Transaction } from '../../interfaces/transaction.model';

@Component({
    selector: 'app-tx-list',
    templateUrl: './tx-list.html',
    styleUrls: ['./tx-list.css'],
    imports: [CommonModule, FormsModule],
})

export class TxListComponent implements OnInit, OnDestroy {
    txService = inject(TransactionService);

    transactions = signal<Transaction[]>([]);
    rbfTxId = signal<number | null>(null);
    newFee = signal<number | null>(null);
    rbfLoading = signal(false);
    rbfError = signal('');

    private pollSub?: Subscription;

    ngOnInit(): void {
    this.pollSub = interval(30_000)
        .pipe(
        startWith(0),
        switchMap(() => this.txService.getTransactions())
        )
        .subscribe({ next: (txs) => this.transactions.set(txs) });
    }

    ngOnDestroy(): void {
    this.pollSub?.unsubscribe();
    }

    refresh(): void {
    this.txService.getTransactions().subscribe({
        next: (txs) => this.transactions.set(txs),
    });
    }

    openRbf(tx: Transaction): void {
    this.rbfTxId.set(tx.id);
    this.newFee.set(Math.ceil(tx.feeSatPerVB) + 5);
    this.rbfError.set('');
    }

    cancelRbf(): void {
    this.rbfTxId.set(null);
    this.newFee.set(null);
    this.rbfError.set('');
    }

    submitRbf(tx: Transaction): void {
    if (!this.newFee()) return;
    this.rbfLoading.set(true);
    this.rbfError.set('');

    this.txService.bumpFee(tx.id, this.newFee()!).subscribe({
        next: () => {
        this.rbfLoading.set(false);
        this.cancelRbf();
        this.refresh();
        },
        error: (err) => {
        this.rbfError.set(err.error?.error ?? 'RBF failed.');
        this.rbfLoading.set(false);
        },
    });
    }

    mempoolUrl(txid: string): string {
    return `https://mempool.space/testnet4/tx/${txid}`;
    }

    getStatusColor(status: string): string {
        if (status == "pending") {
            return "yellow"
        } else if (status == "confirmed") {
            return "green"
        } else if (status == "replaced") {
            return "gray"
        } else {
            return "red"
        }
    }
}