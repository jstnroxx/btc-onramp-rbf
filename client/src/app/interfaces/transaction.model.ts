export interface WalletInfo {
  address: string;
  balanceSat: number;
}

export interface Transaction {
  id: number;
  txId: string;
  recipient: string;
  amountSat: number;
  feeSatPerVB: number;
  sizeBytes: number;
  status: 'pending' | 'confirmed' | 'replaced';
  confirmations: number;
  createdAt: string;
  replacedBy_id: number | null;
  replaces_txId: string | null;
}