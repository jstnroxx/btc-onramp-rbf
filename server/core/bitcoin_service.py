import requests

from bit import PrivateKeyTestnet
from bit.exceptions import InsufficientFunds

MEMPOOL_API_URL = "https://mempool.space/testnet4/api"

# Wallets
def loadWallet(wifKey : str) -> PrivateKeyTestnet:
    try:
        return PrivateKeyTestnet(wifKey)
    except Exception:
        raise ValueError("Invalid WIF key.") 
    
def getWalletInfo(wifKey : str) -> dict:
    wallet = loadWallet(wifKey)
    balanceSat = wallet.get_balance("satoshi")
    
    return {
        "address" : wallet.address,
        "balanceSat" : balanceSat
    }
    
# Network
def getRecommendedFee() -> int:
    response = requests.get(f"{MEMPOOL_API_URL}/v1/fees/recommended", timeout = 10)
    response.raise_for_status()
    
    return response.json().get("fastestFee", 10)

def broadcastTransaction(rawHex : str) -> str:
    response = requests.post(
        f"{MEMPOOL_API_URL}/tx",
        data = rawHex,
        headers = {"Content-Type" : "text/plain"},
        timeout = 15
    )
    response.raise_for_status()
    
    return response.text.strip()

def getTxInfo(txid : str) -> dict | None:
    response = requests.get(f"{MEMPOOL_API_URL}/tx/{txid}", timeout = 10)
    
    if response.status_code == 404:
        return None
    response.raise_for_status()
    
    data = response.json()
    txStatus = data.get("status", {})
    
    return {
        "confirmed" : txStatus.get("confirmed", False),
        "blockHeight" : txStatus.get("block_height"),
        "size" : data.get("size", 0),
        "fee" : data.get("fee", 0)
    }
    
# Transactions
def sendTransaction(wifKey : str, recipient : str, amountSat : int, feeSatPerVB : int) -> dict:
    wallet = loadWallet(wifKey)
    outputs = [(recipient, amountSat, 'satoshi')]
    
    try:
        txHex = wallet.create_transaction(
            outputs,
            fee = feeSatPerVB,
            absolute_fee = False,
            replace_by_fee = True
        )
    except InsufficientFunds:
        raise ValueError("Insufficient funds in this wallet for that amount and fee.")
    
    txId = broadcastTransaction(txHex)
    
    info = getTxInfo(txId)
    size = info["size"] if info else len(txHex) // 2
    
    return {
        "txid" : txId,
        "sizeBytes" : size,
        "feeSatPerVB" : feeSatPerVB
    }
    
def bumpFee(wifKey : str, originalTxId : str, newFeeSatPerVB : int) -> dict:
    from core.models import Transaction
    
    originalTx = Transaction.objects.get(txId = originalTxId)
    
    if newFeeSatPerVB <= originalTx.feeSatPerVB:
        raise ValueError(f"New fee must be greater than the original ({originalTx.feeSatPerVB} sat/vB).")
    
    return sendTransaction(wifKey, originalTx.recipient, originalTx.amountSat, newFeeSatPerVB)

