from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from datetime import datetime


# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
    

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name='email address')
    company_name = models.CharField(max_length=100, blank=True, verbose_name='company name')
    website = models.CharField(max_length=30, blank=True, verbose_name='website')
    phone = models.CharField(max_length=15, blank=True, verbose_name='phone number')
    address = models.TextField(blank=True, verbose_name='address')
    is_active = models.BooleanField(default=True, verbose_name='active')
    is_staff = models.BooleanField(default=False, verbose_name='staff status')
    company_logo = models.ImageField(upload_to='company_logo', null=True, blank=True)
    role = models.CharField(max_length=20, 
                            choices=(
                                ("user","user"),
                                ("manager","manager"),
                                ("admin","admin"),

                            ),
                            default='user'
                            )

    # api managers setting 

    api_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    api_key_added = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    api_expiry = models.DateTimeField(auto_now=False, null=True, blank=True)
    
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name='date joined')
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["company_name","phone"]

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

        
    def __str__(self):
        return str(self.company_name)
    


class User_data_profile(models.Model):
    company = models.OneToOneField(CustomUser, on_delete=models.CASCADE,related_name="company_profile")
    company_profile = models.FileField(upload_to="company_profile", null=True, blank=True)
    products_and_services = models.FileField(upload_to="product_services",null=True, blank=True)
    policies = models.FileField(upload_to="company_policies", null=True, blank=True)

    profile_description = models.TextField(null=True,blank=True)
    products_and_services_description = models.TextField(null=True,blank=True)
    policies_description = models.TextField(null=True,blank=True)


    chatbot_color = models.CharField(max_length=7, default="#ffffff")
    bot_name = models.CharField(max_length=30, default="AI-Bot")
    g_api = models.CharField(max_length=100, null=True, blank=True)


import uuid

class ChatSession(models.Model):
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)

    def __str__(self):
        return f"Session {self.session_id} - {self.client.company_name}"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=[("user", "User"), ("bot", "Bot")])
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message[:30]}"