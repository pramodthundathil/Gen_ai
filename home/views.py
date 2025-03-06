from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import *
from .forms import *
from .decorators import *


from django.views.decorators.clickjacking import xframe_options_exempt


# Create your views here.
@admin_only
@custom_login_required
def index(request):
    return render(request,'index.html')

def user_index(request):
    return render(request,"user_index.html")

def manager_index(request):
    return render(request,"manager_index.html")

def signin(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request,'Invalid username or password')
            return redirect("signin")
    return render(request,"signin.html")

def signout(request):
    logout(request)
    return redirect('landing')


def landing(request):
    return render(request,"landing.html")

@xframe_options_exempt
def amin(request):
    return render(request,'anim.html')

# companies handling from here

def bots(request):
    users = CustomUser.objects.all()
    form =  UserAddForm()

    if request.method == "POST":
        form = UserAddForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.save()
            messages.success(request, "User added successfully.")
            return redirect("update_company", pk = user.id)
        else:
            messages.error(request, form.errors)
            return redirect("bots")

    context = {
        "users":users,
        "form":form
    }
    return render(request,"bots.html",context)

def update_company(request, pk):
    user = get_object_or_404(CustomUser, id = pk)
    if request.method == "POST":
        user.company_name = request.POST.get("company_name", user.company_name)
        user.email = request.POST.get("email", user.email)
        user.phone = request.POST.get("phone", user.phone)
        user.website = request.POST.get("website", user.website)
        user.address = request.POST.get("address", user.address)
        user.role = request.POST.get("role", user.role)
        user.is_active = request.POST.get("is_active") == "True"
        
        # Handle file upload
        if "company_logo" in request.FILES:
            user.company_logo = request.FILES["company_logo"]
        
        # Handle logo removal
        if request.POST.get("remove_logo"):
            user.company_logo.delete(save=False)
            user.company_logo = None
        
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("update_company", pk = pk)  # Redirect to the profile page

    context = {
        "user":user
    }
    return render(request, "update_company.html",context)


import fitz  # PyMuPDF
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User_data_profile, CustomUser

def extract_text_from_pdf(pdf_file):
    """Extracts text from a PDF file."""
    text = ""
    try:
        with fitz.open(pdf_file) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
    except Exception as e:
        print(f"Error extracting text: {e}")
    return text.strip()  # Remove extra spaces

@login_required
def update_user_profile(request, pk):
    user = get_object_or_404(CustomUser, id=pk)

    # Get or create User_data_profile instance
    profile, created = User_data_profile.objects.get_or_create(company=user)

    if request.method == "POST":
        # Check and update uploaded files & extract text
        if "company_profile" in request.FILES:
            profile.company_profile = request.FILES["company_profile"]

        if "products_and_services" in request.FILES:
            profile.products_and_services = request.FILES["products_and_services"]
            

        if "policies" in request.FILES:
            profile.policies = request.FILES["policies"]
            

        # Update chatbot color
        chatbot_color = request.POST.get("chatbot_color", "#ffffff")
        profile.chatbot_color = chatbot_color

        bot_name = request.POST.get("bot_name")

        if bot_name:
            profile.bot_name = bot_name
        # Update Google API Key
        g_api = request.POST.get("g_api")
        if g_api:
            profile.g_api = g_api

        # Save the updated profile
        profile.save()

        try:
            profile.profile_description = extract_text_from_pdf((profile.company_profile.url)[1:])
            print("--------Company")
        except:
            messages.error(request,"No Company Profile")
            print("--------Company error")

        try:
            profile.products_and_services_description = extract_text_from_pdf((profile.products_and_services.url)[1:])
            print("--------product")

        except:
            messages.error(request,"No Services Profile")
            print("--------Product error")

        try:
            profile.policies_description = extract_text_from_pdf((profile.policies.url)[1:])
            print("--------Policy")

        except:
            messages.error(request,"No Policies Profile")
            print("--------policy error")
        
        profile.save()
        messages.success(request, "Data Updated Successfully")
        return redirect("update_company", pk=pk)

    return redirect("update_company", pk=pk)


import uuid
from django.utils.timezone import now
from datetime import timedelta
from .models import CustomUser

@custom_login_required
def generate_api_key(request, pk):
    if request.method == "POST":
        user = get_object_or_404(CustomUser, id = pk)
        expiry_months = int(request.POST.get("expiry_months", 12))  # Default to 12 months

        # Generate a new UUID-based API key
        new_api_key = uuid.uuid4().hex

        # Calculate expiry date
        expiry_date = now() + timedelta(days=30 * expiry_months)

        # Save new API key and expiry date
        user.api_key = new_api_key
        user.api_key_added = now()
        user.api_expiry = expiry_date
        user.save()

        messages.success(request, "API Key has been successfully generated!")
        return redirect("update_company", pk = pk)  # Change "profile" to the actual name of the profile page




# integration of admin chat bot is starting form here 

from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.shortcuts import get_object_or_404
import requests
from .models import  ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, Company_serializer

GEMINI_API_URL = "https://api.gemini.com/v1/chat"  # Update with actual Gemini API URL

import google.generativeai as genai

import re
def preprocess_response(text):
    """
    Preprocess the response to handle markdown-like syntax.
    Converts:
    - ***text*** to <b><i>text</i></b> (bold + italic)
    - **text** to <b>text</b> (bold)
    - *text* to <i>text</i> (italic)
    - Newlines (\n) to <br> for line breaks
    """
    # Handle ***text*** (bold + italic)
    text = re.sub(r"\*\*\*(.*?)\*\*\*", r"<b><i>\1</i></b>", text)

    # Handle **text** (bold)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

    # Handle *text* (italic)
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)

    # Convert newline characters (\n) to <br>
    text = text.replace("\n", "<br>")

    return text

class ChatBotAPI(APIView):
    permission_classes = [AllowAny]  # Change to authentication-based in production

    def post(self, request):
        api_key = request.data.get("api_key")
        user_message = request.data.get("message")
        session_id = request.data.get("session_id")

        if not api_key or not user_message or not session_id:
            return Response({"error": "Missing required fields"}, status=400)
        
        try:
            client = get_object_or_404(CustomUser, api_key=api_key)
        except:
            return Response({"Error":"No Data From Client"})

        # Fetch or create a chat session
        session, _ = ChatSession.objects.get_or_create(client=client, session_id=session_id)

        # Store user message in DB
        ChatMessage.objects.create(session=session, sender="user", message=user_message)

        # Check Redis Cache for past messages
        cache_key = f'chat_history_{session_id}'
        chat_history = cache.get(cache_key, [])

        # Send request to Gemini API
        ai_response = self.get_gemini_response(user_message, chat_history,client )

        # Store AI response
        ChatMessage.objects.create(session=session, sender="bot", message=ai_response)

        # Update Redis cache
        chat_history.append({"sender": "user", "message": user_message})
        chat_history.append({"sender": "bot", "message": ai_response})

        if len(chat_history) > 10:  # Keep only last 10 messages
            chat_history.pop(0)

        cache.set(cache_key, chat_history, timeout=86400)  # 24 hours cache

        return Response({"response": ai_response})
    



    def get_gemini_response(self, user_input, history, client):
        """
        Sends a message to Gemini AI and returns the response.
        
        :param user_input: The user's message.
        :param history: List of previous chat messages.
        :return: AI-generated response.
        """

        g_api_key = client.company_profile.g_api
        # Configure Gemini API
        genai.configure(api_key=g_api_key)  # Replace with actual API key

        # Use Gemini Generative Model
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Prepare chat history in the correct format
        conversation = [{}]

        if history:
            for msg in history:
                conversation.append({
                    "role": "user" if msg["sender"] == "user" else "model",
                    "parts": [{"text": msg["message"]}]
                })
        prompt = """
                       You are {}, the official AI assistant for {}. 

                            COMPANY INFORMATION:
                            {}

                            COMPANY POLICIES:
                            {}

                            PRODUCTS AND SERVICES:
                            {}

                            PREVIOUS CONVERSATION:
                            {}

                            CUSTOMER QUERY:
                            {}

                            RESPONSE GUIDELINES:
                            1. Provide concise, accurate responses (under 3 paragraphs)
                            2. Use "we" instead of "they" when referring to the company
                            3. Maintain a professional, helpful tone
                            4. Only reference information provided above
                            5. Focus on addressing the specific question
                            6. If unable to answer, politely redirect to human support
                            7. Do not fabricate information not included above
                            8. For complex queries, provide clear next steps
                            9. Format responses for easy reading on chat interface

                            CONTACT COLLECTION:
                            1. When appropriate in the conversation flow, naturally ask for customer contact details
                            2. Request information elegantly: "To better assist you, may I have your [contact detail]?"
                            3. Collect only necessary information (name, email, phone) based on context
                            4. Explain briefly why the information is helpful (e.g., "to send you that document" or "for our specialist to follow up")
                            5. Thank customers when they provide information
                            6. Never appear pushy or demand contact details
                            7. If customer seems hesitant, offer to continue without contact information
                            8. Store provided contact details for reference in future responses

                        """.format(client.company_profile.bot_name,client.company_name,client.company_profile.profile_description, client.company_profile.policies_description, client.company_profile.products_and_services_description,conversation, user_input)

        # Generate AI response
        response = model.generate_content(prompt)
        
        # Process AI response
        if response and hasattr(response, "text"):  # Ensure response has text attribute
            ai_response = preprocess_response(response.text)
            return ai_response
        else:
            return "Sorry, I couldn't process that."

@api_view(["POST"])
def customer_details(request):
    api = request.data.get("api_key")
    try:
        company_profile = get_object_or_404(User_data_profile, company__api_key = api)
        serializer = Company_serializer(instance = company_profile)
        return Response(serializer.data)

    except:
        return Response({"message":"No Company profile Find"}) 
      



from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
# from weasyprint import HTML
from .models import ChatSession, CustomUser
from django.template.loader import render_to_string

def generate_full_chat_report(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    sessions = ChatSession.objects.filter(client=user).prefetch_related("messages")

    # # Render the HTML template with chat data
    html_string = render_to_string('chat_report_template.html', {'user': user, 'sessions': sessions})

    # # Generate the PDF from HTML
    # pdf = HTML(string=html_string).write_pdf()

    # # Create a response with PDF content
    response = HttpResponse(html_string, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="chat_report_{user.company_name}.pdf"'

    return response


# django functions analytics

# analytics.py - Place this in your Django app folder

from django.db.models import Count, Avg, Sum, F, ExpressionWrapper, fields, Q
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser, ChatSession, ChatMessage
import io
from django.http import FileResponse
# from reportlab.pdfgen import canvas
# from reportlab.lib.units import inch
# from reportlab.lib.pagesizes import letter
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet

def get_user_chat_statistics(user_id=None, time_period=None):
    """
    Get chat statistics for a specific user or all users
    
    Parameters:
    user_id (int): ID of the user to get statistics for. If None, get for all users.
    time_period (str): 'day', 'week', 'month', 'year', or None for all time
    
    Returns:
    dict: Dictionary of user statistics
    """
    # Base queryset for users
    users_qs = CustomUser.objects.all()
    
    # Filter by user ID if provided
    if user_id:
        users_qs = users_qs.filter(id=user_id)
    
    # Create date filter based on time period
    date_filter = {}
    if time_period:
        now = timezone.now()
        if time_period == 'day':
            date_filter = {'timestamp__gte': now - timedelta(days=1)}
        elif time_period == 'week':
            date_filter = {'timestamp__gte': now - timedelta(weeks=1)}
        elif time_period == 'month':
            date_filter = {'timestamp__gte': now - timedelta(days=30)}
        elif time_period == 'year':
            date_filter = {'timestamp__gte': now - timedelta(days=365)}
    
    # Initialize results list
    results = []
    
    for user in users_qs:
        # Get all sessions for this user
        sessions = ChatSession.objects.filter(client=user)
        
        # Get total sessions count
        total_sessions = sessions.count()
        
        # Get all messages in these sessions
        messages_query = ChatMessage.objects.filter(session__in=sessions)
        
        # Apply time filter if needed
        if date_filter:
            messages_query = messages_query.filter(**date_filter)
        
        # Calculate statistics
        total_messages = messages_query.count()
        user_messages = messages_query.filter(sender='user').count()
        bot_messages = messages_query.filter(sender='bot').count()
        
        # Get the date of the last activity
        last_activity = messages_query.order_by('-timestamp').first()
        last_activity_date = last_activity.timestamp if last_activity else None
        
        # Get average messages per session
        avg_messages_per_session = total_messages / total_sessions if total_sessions > 0 else 0
        
        # Get active sessions (sessions with activity in the selected time period)
        active_sessions = 0
        if date_filter:
            active_sessions = sessions.filter(
                messages__timestamp__gte=date_filter['timestamp__gte']
            ).distinct().count()
        else:
            active_sessions = total_sessions
        
        # Create user stats dictionary
        user_stats = {
            'user_id': user.id,
            'company_name': user.company_name,
            'email': user.email,
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'total_messages': total_messages,
            'user_messages': user_messages,
            'bot_messages': bot_messages,
            'avg_messages_per_session': round(avg_messages_per_session, 2),
            'last_activity': last_activity_date,
        }
        
        results.append(user_stats)
    
    return results

def get_detailed_user_statistics(user_id):
    """
    Get detailed statistics for a specific user including daily/weekly activity
    
    Parameters:
    user_id (int): ID of the user to get statistics for
    
    Returns:
    dict: Dictionary of detailed user statistics
    """
    user = CustomUser.objects.get(id=user_id)
    sessions = ChatSession.objects.filter(client=user)
    
    # Get all messages for this user
    messages = ChatMessage.objects.filter(session__in=sessions)
    
    # Calculate daily message counts for the last 30 days
    now = timezone.now()
    daily_stats = []
    
    for i in range(30, 0, -1):
        day_date = now - timedelta(days=i)
        next_day = day_date + timedelta(days=1)
        
        day_messages = messages.filter(
            timestamp__gte=day_date,
            timestamp__lt=next_day
        ).count()
        
        daily_stats.append({
            'date': day_date.date(),
            'count': day_messages
        })
    
    # Calculate weekly message counts
    weekly_stats = []
    
    for i in range(12, 0, -1):
        week_start = now - timedelta(weeks=i)
        week_end = week_start + timedelta(weeks=1)
        
        week_messages = messages.filter(
            timestamp__gte=week_start,
            timestamp__lt=week_end
        ).count()
        
        weekly_stats.append({
            'week': f"Week {i} ago",
            'count': week_messages
        })
    
    # Get the 5 most active sessions
    top_sessions = []
    for session in sessions:
        message_count = ChatMessage.objects.filter(session=session).count()
        session_data = {
            'session_id': session.session_id,
            'created_at': session.messages.order_by('timestamp').first().timestamp if session.messages.exists() else None,
            'message_count': message_count
        }
        top_sessions.append(session_data)
    
    # Sort by message count and take top 5
    top_sessions = sorted(top_sessions, key=lambda x: x['message_count'], reverse=True)[:5]
    
    return {
        'user': user,
        'total_sessions': sessions.count(),
        'total_messages': messages.count(),
        'daily_stats': daily_stats,
        'weekly_stats': weekly_stats,
        'top_sessions': top_sessions
    }

def generate_pdf_report(user_id=None):
    """
    Generate a PDF report of user chat statistics
    
    Parameters:
    user_id (int): ID of the user to generate report for. If None, generate for all users.
    
    Returns:
    FileResponse: PDF file response
    """
    # # Get statistics
    # stats = get_user_chat_statistics(user_id)
    
    # # Create buffer for PDF file
    # buffer = io.BytesIO()
    
    # # Create PDF document
    # doc = SimpleDocTemplate(buffer, pagesize=letter)
    # elements = []
    
    # # Add styles
    # styles = getSampleStyleSheet()
    # title_style = styles['Title']
    # heading_style = styles['Heading2']
    # normal_style = styles['Normal']
    
    # # Add title
    # if user_id:
    #     user = CustomUser.objects.get(id=user_id)
    #     elements.append(Paragraph(f"Chat Analytics Report - {user.company_name}", title_style))
    # else:
    #     elements.append(Paragraph("Chat Analytics Report - All Users", title_style))
    
    # elements.append(Spacer(1, 0.25*inch))
    # elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    # elements.append(Spacer(1, 0.5*inch))
    
    # # Create table data
    # if user_id:
    #     elements.append(Paragraph("User Information", heading_style))
    #     elements.append(Spacer(1, 0.25*inch))
        
    #     user_info = [
    #         ["Company Name", stats[0]['company_name']],
    #         ["Email", stats[0]['email']],
    #         ["Total Sessions", stats[0]['total_sessions']],
    #         ["Total Messages", stats[0]['total_messages']],
    #         ["User Messages", stats[0]['user_messages']],
    #         ["Bot Messages", stats[0]['bot_messages']],
    #         ["Avg Messages Per Session", stats[0]['avg_messages_per_session']],
    #         ["Last Activity", stats[0]['last_activity'].strftime('%Y-%m-%d %H:%M') if stats[0]['last_activity'] else "N/A"]
    #     ]
        
    #     user_table = Table(user_info, colWidths=[2*inch, 4*inch])
    #     user_table.setStyle(TableStyle([
    #         ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    #         ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
    #         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    #         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    #         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    #         ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    #         ('GRID', (0, 0), (-1, -1), 1, colors.black)
    #     ]))
        
    #     elements.append(user_table)
    # else:
    #     elements.append(Paragraph("All Users Statistics", heading_style))
    #     elements.append(Spacer(1, 0.25*inch))
        
    #     # Create table header
    #     table_data = [
    #         ["Company", "Total Sessions", "Total Messages", "User Msgs", "Bot Msgs", "Avg Msgs/Session", "Last Activity"]
    #     ]
        
    #     # Add data rows
    #     for user_stat in stats:
    #         table_data.append([
    #             user_stat['company_name'],
    #             str(user_stat['total_sessions']),
    #             str(user_stat['total_messages']),
    #             str(user_stat['user_messages']),
    #             str(user_stat['bot_messages']),
    #             str(user_stat['avg_messages_per_session']),
    #             user_stat['last_activity'].strftime('%Y-%m-%d') if user_stat['last_activity'] else "N/A"
    #         ])
        
    #     # Create table and style
    #     users_table = Table(table_data)
    #     users_table.setStyle(TableStyle([
    #         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    #         ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
    #         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    #         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    #         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    #         ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    #         ('GRID', (0, 0), (-1, -1), 1, colors.black)
    #     ]))
        
    #     elements.append(users_table)
    
    # # Build PDF and save to buffer
    # doc.build(elements)
    # buffer.seek(0)
    
    # # Create file response
    # return FileResponse(buffer, as_attachment=True, filename='chat_analytics_report.pdf')


# views.py - Add these functions to your existing views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import CustomUser, ChatSession, ChatMessage
# from .analytics import get_user_chat_statistics, get_detailed_user_statistics, generate_pdf_report

@login_required
def analytics_dashboard(request):
    """View for the main analytics dashboard"""
    # Get time period from query parameters (default to 'month')
    time_period = request.GET.get('time_period', 'month')
    
    # Get user statistics based on current user's role
    user = request.user
    
    if user.role == 'admin':
        # Admin can see all users' statistics
        user_stats = get_user_chat_statistics(time_period=time_period)
    else:
        # Regular users can only see their own statistics
        user_stats = get_user_chat_statistics(user_id=user.id, time_period=time_period)
    
    context = {
        'user_stats': user_stats,
        'time_period': time_period,
        'is_admin': user.role == 'admin',
    }
    
    return render(request, 'analytics_dashboard.html', context)

@login_required
def user_detailed_analytics(request, user_id):
    """View for detailed analytics of a specific user"""
    # Check permissions
    if request.user.role != 'admin' and request.user.id != int(user_id):
        return redirect('analytics_dashboard')
    
    # Get detailed statistics
    detailed_stats = get_detailed_user_statistics(user_id)
    
    context = {
        'detailed_stats': detailed_stats,
        'is_admin': request.user.role == 'admin',
    }
    
    return render(request, 'user_detailed_analytics.html', context)

@login_required
def download_analytics_pdf(request):
    """View to download analytics as PDF"""
    # Determine if specific user or all users
    user_id = request.GET.get('user_id', None)
    
    # Check permissions
    if user_id and request.user.role != 'admin' and request.user.id != int(user_id):
        return redirect('analytics_dashboard')
    
    # If user is not admin and trying to download all users' report, restrict to their own
    if request.user.role != 'admin' and not user_id:
        user_id = request.user.id
    
    # Generate PDF
    return generate_pdf_report(user_id)

# Add API endpoint for chart data
@login_required
def get_chart_data(request, user_id):
    """API endpoint to get chart data for a specific user"""
    # Check permissions
    if request.user.role != 'admin' and request.user.id != int(user_id):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get detailed statistics
    detailed_stats = get_detailed_user_statistics(user_id)
    
    # Format data for charts
    daily_data = [{'date': str(day['date']), 'count': day['count']} for day in detailed_stats['daily_stats']]
    weekly_data = [{'week': week['week'], 'count': week['count']} for week in detailed_stats['weekly_stats']]
    
    return JsonResponse({
        'daily_data': daily_data,
        'weekly_data': weekly_data
    })