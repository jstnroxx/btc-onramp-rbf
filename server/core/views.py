from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Transaction
from .serializers import TransactionSerializer
from . import bitcoin_service

def _requireKey(request) -> str | None:
    return request.data.get("wifKey") or None

class WalletInfoView(APIView):
    def post(self, request):
        wifKey = _requireKey(request)
        
        if not wifKey:
            return Response({'error' : 'wifKey is required'}, status = status.HTTP_400_BAD_REQUEST)
        
        try:
            info = bitcoin_service.getWalletInfo(wifKey)
        except ValueError as err:
            return Response({'error' : str(err)}, status = status.HTTP_400_BAD_REQUEST)
        
        return Response(info)
    
class RecommendedFeeView(APIView):
    def get(self, request):
        fee = bitcoin_service.getRecommendedFee()
        
        return Response({'feeSatPerVB' : fee})
    
class TransactionListView(APIView):
    def get(self, request):
        transactions = Transaction.objects.all().order_by('-createdAt')
        
        for tx in transactions:
            if tx.status == Transaction.Status.PENDING:
                info = bitcoin_service.getTxInfo(tx.txId)
                
                if info is None:
                    if not tx.replacedBy:
                        tx.status = Transaction.Status.REPLACED
                        tx.save(update_fields = ['status'])
                elif info["confirmed"]:
                    tx.confirmations = 1
                    tx.status = Transaction.Status.CONFIRMED
                    tx.save(update_fields = ['confirmations', 'status'])
                    
        return Response(TransactionSerializer(transactions, many = True).data)
    
    def post(self, request):
        wifKey = _requireKey(request)
        recipient = request.data.get("recipient")
        amountSat = request.data.get("amountSat")
        fee = request.data.get("feeSatPerVB")
        
        if not all([wifKey, recipient, amountSat]):
            return Response({'error' : 'wifKey, recipient, amountSat are required'}, status = status.HTTP_400_BAD_REQUEST)
        
        if not fee:
            fee = bitcoin_service.getRecommendedFee()
            
        try:
            result = bitcoin_service.sendTransaction(wifKey, recipient, amountSat, fee)
        except Exception as err:
            return Response({'error' : str(err)}, status = status.HTTP_400_BAD_REQUEST)
        
        tx = Transaction.objects.create(
            txId = result["txId"],
            recipient = recipient,
            amountSat = int(amountSat),
            feeSatPerVB = int(fee),
            sizeBytes = result["sizeBytes"]
        )
        
        return Response(TransactionSerializer(tx).data, status = status.HTTP_201_CREATED)
    
class RBFView(APIView):
    def post(self, request, pk):
        wifKey = _requireKey(request)
        newFee = request.data.get("newFeeSatPerVB")
        
        if not wifKey or not newFee:
            return Response({'error' : 'wifKey and newFeeSatPerVB are required'}, status = status.HTTP_400_BAD_REQUEST)
        
        try:
            originalTx = Transaction.objects.get(pk = pk)
        except Transaction.DoesNotExist:
            return Response({'error' : 'Transaction not found'}, status = status.HTTP_404_NOT_FOUND)
        
        if originalTx.status != Transaction.Status.PENDING:
            return Response({'error' : 'Only pending transactions can be fee-bumped'}, status = status.HTTP_400_BAD_REQUEST)
        
        try:
            result = bitcoin_service.bumpFee(wifKey, originalTx.txId, int(newFee))
        except Exception as err:
            return Response({'error' : str(err)}, status = status.HTTP_400_BAD_REQUEST)    
        
        newTx = Transaction.objects.create(
            txId = result["txId"],
            recipient = originalTx.recipient,
            amountSat = originalTx.amountSat,
            feeSatPerVB = result["feeSatPerVB"],
            sizeBytes = result["sizeBytes"]
        )
        
        originalTx.replacedBy = newTx
        originalTx.status = Transaction.Status.REPLACED
        originalTx.save(update_fields = ['replacedBy', 'status'])
        
        return Response({
            'original' : TransactionSerializer(originalTx).data,
            'replacement' : TransactionSerializer(newTx).data
        }, status = status.HTTP_201_CREATED)