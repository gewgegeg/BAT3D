from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    isAdmin = serializers.SerializerMethodField(method_name='get_admin_status')
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'phone', 'address', 'is_staff', 'is_superuser', 'is_active', 'isAdmin')
        read_only_fields = ('id', 'is_superuser', 'isAdmin')
    
    def get_admin_status(self, obj):
        return obj.is_staff or obj.is_superuser

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2', 'phone', 'address')
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError(_("Passwords don't match."))
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user 