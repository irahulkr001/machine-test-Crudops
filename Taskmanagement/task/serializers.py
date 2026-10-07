from rest_framework import serializers
from django.contrib.auth.models import User
from task.models import Task

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,min_length=6)
    class Meta:
        model = User
        fields = ['username','email','password']

    def create(self, validated_data):
        user=User.objects.create_user(username=validated_data['username'],email=validated_data['email'],password=validated_data['password'])
        return user

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id','title','description','status','priority','due_date','created_date']
        read_only_fields = ['id','created_date']

class LoginSerializer(serializers.Serializer):

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)