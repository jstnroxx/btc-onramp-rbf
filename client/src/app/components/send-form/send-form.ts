import { Component, inject, signal, output, OnInit, effect } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { TransactionService } from '../../services/transaction';

@Component({
  selector: 'app-send-form',
  standalone: true,
  templateUrl: './send-form.html',
  styleUrls: ['./send-form.css'],
  imports: [FormsModule, CommonModule],
})

export class SendFormComponent implements OnInit {
  readonly sent = output<void>();

  txService = inject(TransactionService);

  recipient = signal('');
  amountSat = signal<number | null>(null);
  feeSatPerVb = signal<number | null>(null);
  recommendedFee = signal<number | null>(null);
  loading = signal(false);
  error = signal('');

  constructor() {
    effect(() => {
        if (!this.txService.isWalletConnected()) {
        this.recipient.set('');
        this.amountSat.set(null);
        this.feeSatPerVb.set(null);
        this.error.set('');
        }
    });
    }

  ngOnInit(): void {
    this.txService.getRecommendedFee().subscribe({
      next: (res) => {
        this.recommendedFee.set(res.feeSatPerVB);
        this.feeSatPerVb.set(res.feeSatPerVB);
      },
    });
  }

  send(): void {
    if (!this.recipient() || !this.amountSat()) return;
    const fee = this.feeSatPerVb() ?? this.recommendedFee() ?? 10;

    this.loading.set(true);
    this.error.set('');

    this.txService.sendTransaction(this.recipient(), this.amountSat()!, fee).subscribe({
      next: () => {
        this.loading.set(false);
        this.recipient.set('');
        this.amountSat.set(null);
        this.feeSatPerVb.set(this.recommendedFee());
        this.sent.emit();
      },
      error: (err) => {
        this.error.set(err.error?.error ?? 'Failed to send transaction.');
        this.loading.set(false);
      },
    });
  }
}