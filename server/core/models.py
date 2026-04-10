from django.db import models

class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        REPLACED = 'replaced', 'Replaced'
        
    txId = models.CharField(max_length = 64, unique = True)
    recipient = models.CharField(max_length = 100)
    amountSat = models.BigIntegerField()
    feeSatPerVB = models.FloatField()
    sizeBytes = models.IntegerField(default = 0)
    status = models.CharField(max_length = 20, choices = Status.choices, default = Status.PENDING)
    confirmations = models.IntegerField(default = 0)
    createdAt = models.DateTimeField(auto_now_add = True)
    
    replacedBy = models.OneToOneField(
        'self', null = True, blank = True,
        on_delete = models.SET_NULL,
        related_name = "replaces"
    )
    
    def __str__(self):
        return f"Transaction: {self.txId[:12]}... ({self.status})"