import requests

from bitcoinlib.keys import Key
from bitcoinlib.transactions import Transaction
from bitcoinlib.services.services import Service

MEMPOOL_API_URL = "https://mempool.space/testnet4/api"

# Wallets
def _getWitnessType(key : Key) -> tuple[str, str]:
    btcService = Service(network = "testnet4")
    
    segwitAddress = key.address(encoding = "bech32")
    legacyAddress = key.address(encoding = "base58")
    
    if btcService.getutxos(segwitAddress):
        return segwitAddress, "segwit"
    
    if btcService.getutxos(legacyAddress):
        return legacyAddress, "legacy"
    
    return segwitAddress, "segwit"

def loadWallet(wifKey : str) -> Key:
    try:
        key = Key(wifKey, network = "testnet4")
    except:
        raise ValueError("Invalid WIF key") 
    
    address, witnessType = _getWitnessType(key)
    return key, address, witnessType
    
def getWalletInfo(wifKey : str) -> dict:
    key, address, witnessType = loadWallet(wifKey)
    
    btcService = Service(network = "testnet4")
    balanceSat = btcService.getbalance(address)
    
    return {
        "address" : address,
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
    
    if not response.ok:
        raise ValueError(response.text)
    
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
def sendTransaction(wifKey : str, recipient : str, amountSat : int, feeSatPerVB : int, forcedUtxos: list | None = None) -> dict:
    key, address, witnessType = loadWallet(wifKey)
    
    btcService = Service(network = "testnet4")
    addressUtxos = forcedUtxos if forcedUtxos is not None else btcService.getutxos(address)
    
    if not addressUtxos:
        raise ValueError("No UTXOs found. Is the wallet funded?")
    
    tx = Transaction(network = "testnet4", witness_type = witnessType)
    
    totalInputSat = 0
    
    for utxo in addressUtxos:
        tx.add_input(prev_txid = utxo["txid"], output_n = utxo["output_n"], keys = [key], sequence = 0xFFFFFFFD, witness_type = witnessType)    # "sequence = 0xFFFFFFFD" enables RBF
        totalInputSat += utxo["value"]
        
        estimatedSize = tx.estimate_size()
        requiredFee = estimatedSize * feeSatPerVB
        
        if totalInputSat >= (amountSat + requiredFee):
            break
    else:
        raise ValueError("Insufficient funds in this wallet for that amount and fee.")
    
    tx.add_output(amountSat, address = recipient)
    
    finalSize = tx.estimate_size()
    finalFee = finalSize * feeSatPerVB
    changeAmount = totalInputSat - amountSat - finalFee
    
    if changeAmount > 546:    # 546 satoshi is bitcoin dust limit, do not send such changes below
        tx.add_output(changeAmount, address = address)
        
    tx.sign()    
    
    rawTxHex = tx.raw_hex()
    
    txId = broadcastTransaction(rawTxHex)
    
    info = getTxInfo(txId)
    size = info["size"] if info else len(rawTxHex) // 2
    
    return {
        "txId" : txId,
        "sizeBytes" : size,
        "feeSatPerVB" : feeSatPerVB
    }
    
def bumpFee(wifKey : str, originalTxId : str, newFeeSatPerVB : int) -> dict:
    from core.models import Transaction as TransactionModel
    
    originalTx = TransactionModel.objects.get(txId = originalTxId)
    
    if newFeeSatPerVB <= originalTx.feeSatPerVB:
        raise ValueError(f"New fee must be greater than the original ({originalTx.feeSatPerVB} sat/vB).")
    
    response = requests.get(f"{MEMPOOL_API_URL}/tx/{originalTxId}", timeout = 10)
    if not response.ok:
        raise ValueError("Original transaction not found in mempool.")
    
    originalTxData = response.json()
    
    forcedUtxos = []
    for intake in originalTxData.get("vin", []):
        parentResponse = requests.get(f"{MEMPOOL_API_URL}/tx/{intake["txid"]}", timeout = 10)
        parentResponse.raise_for_status()
        parentOutput = parentResponse.json()["vout"][intake["vout"]]
        
        forcedUtxos.append({
            "txid" : intake["txid"],
            "output_n" : intake["vout"],
            "value" : parentOutput["value"] 
        })
        
    return sendTransaction(wifKey, originalTx.recipient, originalTx.amountSat, newFeeSatPerVB, forcedUtxos = forcedUtxos)

def _getCurrentBlockHeight() -> int | None:
    try:
        response = requests.get(f"{MEMPOOL_API_URL}/blocks/tip/height", timeout = 10)
        response.raise_for_status()
        
        return int(response.text.strip())
    except:
        return None
    
def refreshConfirmations(transactions) -> None:
    currentHeight = _getCurrentBlockHeight()
    
    for tx in transactions:
        info = getTxInfo(tx.txId)
        
        if info is None:
            if not tx.replacedBy:
                tx.status = "replaced"
                tx.save(update_fields = ["status"])
        elif info["confirmed"] and info["blockHeight"] and currentHeight:
            tx.confirmations = currentHeight - info["blockHeight"] + 1
            tx.status = "confirmed"
            tx.save(update_fields = ["confirmations", "status"])
        
        