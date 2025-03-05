from rest_framework import serializers
from .models import ChatSession, ChatMessage, User_data_profile, CustomUser

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["sender", "message", "timestamp"]
        

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ["session_id", "messages"]


class Company_details_serializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["company_name","website","company_logo"]

class Company_serializer(serializers.ModelSerializer):
    company = Company_details_serializer(read_only = True)
    class Meta:
        model = User_data_profile
        fields = ["company", "chatbot_color", "bot_name"] 