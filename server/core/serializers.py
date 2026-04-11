from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    replaces_txId = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = ["id", "txId", "recipient", "amountSat", "feeSatPerVB", "sizeBytes", "status", "confirmations", "createdAt", "replacedBy_id", "replaces_txId"]
        
    def get_replaces_txId(self, obj):
        if hasattr(obj, "replaces") and obj.replaces:
            return obj.replaces.txId
        
        return None