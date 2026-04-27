from django.db import models


class ServiceRecord(models.Model):
    """Model to store service records for vehicles"""
    customer_name = models.CharField(max_length=100)
    mechanic_name = models.CharField(max_length=100)
    vehicle_number = models.CharField(max_length=50)
    service_date = models.DateField()
    mongo_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'service_records'
    
    def __str__(self):
        return f"{self.customer_name} - {self.vehicle_number} ({self.service_date})"


class ServiceItem(models.Model):
    """Model to store individual service items for a service record"""
    record = models.ForeignKey(ServiceRecord, on_delete=models.CASCADE, related_name='items')
    changes = models.TextField(blank=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        db_table = 'service_items'
    
    def __str__(self):
        return f"Service Item {self.order} for {self.record.customer_name}"
