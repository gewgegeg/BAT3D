from rest_framework import serializers
from .models import ServiceInquiry
from products.models import PrintingService

class ServiceInquirySerializer(serializers.ModelSerializer):
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=PrintingService.objects.all(),
        source='service',
        write_only=True,
        allow_null=True, # Allow inquiries not tied to a specific service
        required=False
    )
    service_name = serializers.CharField(source='service.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ServiceInquiry
        fields = [
            'id', 'service', 'service_id', 'service_name', 'name', 'email', 'phone', 
            'message', 'status', 'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status_display', 'service_name']
        # 'service' field is read_only by default because of service_id write_only field.
        # We only expose service_id for writing and service (nested) for reading.

    def to_representation(self, instance):
        # Customize representation to show full service details if needed, or just name
        representation = super().to_representation(instance)
        # If you want to show the full PrintingService object on read:
        # from products.serializers import PrintingServiceSerializer # Avoid circular import if moved
        # representation['service'] = PrintingServiceSerializer(instance.service).data if instance.service else None
        # For now, service_name is sufficient as per fields definition.
        # Remove the default 'service' pk representation if service_name is preferred on read and service_id for write
        if 'service' in representation and representation['service'] is None and instance.service is None:
             pass # keep it None
        elif 'service' in representation and instance.service:
            representation['service'] = instance.service.id # Or a more detailed dict if needed
        return representation 