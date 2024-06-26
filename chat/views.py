import os
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from groq import Groq
from django.views.decorators.csrf import csrf_exempt
from django.core.signing import Signer, BadSignature
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from .forms import SignUpForm, OTPVerificationForm, SignInForm
from .models import Otp, User
import datetime
from django.core.mail import send_mail
from django.utils import timezone
from django.shortcuts import render, HttpResponse, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
import random
import string
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from dotenv import load_dotenv

signer = Signer()

load_dotenv()

def home(request):
    return render(request, "chat/home.html")



@login_required(login_url=reverse_lazy('chat:sign_in_or_sign_up'))
@csrf_exempt
def chat_view(request):
    if 'conversation' not in request.session:
        username = request.user.username if request.user.is_authenticated else "there"
        request.session['conversation'] = [
            {
                "role": "system",
                "content": "You are an AI assistant knowledgeable about Y Combinator. You hold all the information from Y Combinator's YouTube channel and understand Y Combinator's ideology. You interact like a human from Y Combinator, engaging in a conversational manner. When discussing startups, you can criticize, ask relevant questions such as 'How do you think you can scale it?', 'What is your budget?', and other critical aspects of startup development,one by one. you can also tell if you think the idea is not good after listening more about the idea one by one, after listening to the user. reply in a short way"
            },
            {
                "role": "assistant",
                "content": f"Hello {username},  What is your startup idea ?"
            }
        ]

    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user_message = request.POST.get("message")

        conversation = request.session['conversation']
        conversation.append({"role": "user", "content": user_message})

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        chat_completion = client.chat.completions.create(
            messages=conversation,
            model="llama3-8b-8192",
        )
        response_message = chat_completion.choices[0].message.content

        conversation.append({"role": "assistant", "content": response_message})

        request.session['conversation'] = conversation

        return JsonResponse({"response_message": response_message})

    return render(request, "chat/chat.html")




@csrf_exempt
def clear_session(request):
    if 'conversation' in request.session:
        del request.session['conversation']
    return HttpResponse(status=200)

def get_conversation(request):
    conversation = request.session.get('conversation', [])
    filtered_conversation = [msg for msg in conversation if msg['role'] != 'system']
    return JsonResponse(filtered_conversation, safe=False)


@login_required(login_url=reverse_lazy('chat:sign_in_or_sign_up'))
@csrf_exempt
def interview_view(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        username = request.user.username if request.user.is_authenticated else "there"
        user_message = request.POST.get("message")
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

        context = request.session.get('conversation_context', [
            {"role": "system", "content": f"You are a AI Powered Y Combinator interviewer,your name is YCMatter AI, you are talking to {username}, based on all data of how the YC interview works you can ask questions, be polite and respond shorter"}
        ])
        
        context.append({"role": "user", "content": user_message})
        
        try:
            chat_completion = client.chat.completions.create(
                messages=context,
                model="llama3-8b-8192",
            )
            response_message = chat_completion.choices[0].message.content
            context.append({"role": "assistant", "content": response_message})
            request.session['conversation_context'] = context
            
            return JsonResponse({"response_message": response_message})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return render(request, "chat/interview_chat.html")

@login_required(login_url=reverse_lazy('chat:sign_in_or_sign_up'))
@csrf_exempt
def clear_interview_context_view(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            if 'conversation_context' in request.session:
                del request.session['conversation_context']  # Clear only the conversation context
            return JsonResponse({"message": "Conversation context cleared successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)


def contact(request):
    return render(request,'contact.html')

@method_decorator(csrf_exempt, name='dispatch')
class ContactFormView(View):
    def post(self, request):
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if not name or not email or not message:
            return JsonResponse({'success': False, 'message': 'All fields are required.'})

        subject = f'Contact Form Submission from {name}'
        body = f'Name: {name}\nEmail: {email}\n\nMessage:\n{message}'
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])
            return JsonResponse({'success': True, 'message': 'Your message has been sent successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

def about(request):
    return render(request,'about.html')

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It is valid for 1 minute.'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)

@csrf_exempt
def sign_in_or_sign_up(request):
    if request.method == 'POST':
        if 'sign-in' in request.POST:
            email = request.POST.get('email')
            user = User.objects.filter(email=email).first()
            if user:
                otp = generate_otp()
                expiry_time = timezone.now() + datetime.timedelta(minutes=10)
                Otp.objects.update_or_create(email=email, defaults={'otp': otp, 'expiry_time': expiry_time})
                send_otp_email(email, otp)
                signed_email = signer.sign(email)
                return redirect('chat:verify_otp', signed_email=signed_email)
            else:
                messages.error(request, 'Email not found. Please sign up.')

        elif 'sign-up' in request.POST:
            username = request.POST.get('username')
            email = request.POST.get('email')
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered. Please sign in.')
            else:
                otp = generate_otp()
                expiry_time = timezone.now() + datetime.timedelta(minutes=10)
                Otp.objects.update_or_create(email=email, defaults={'otp': otp, 'expiry_time': expiry_time})
                send_otp_email(email, otp)
                messages.success(request, 'OTP sent to your email. Please verify to complete registration.')
                signed_email = signer.sign(email)
                signed_username = signer.sign(username)
                return redirect('chat:verify_otp_signup', signed_email=signed_email, signed_username=signed_username)

    return render(request, 'login.html')


def verify_otp(request, signed_email):
    try:
        email = signer.unsign(signed_email)
    except BadSignature:
        messages.error(request, 'Invalid or tampered data.')
        return render(request, 'verify_otp.html')

    if request.method == 'POST':
        otp = request.POST.get('otp')
        otp_record = Otp.objects.filter(email=email).first()
        if otp_record and otp_record.otp == otp and not otp_record.is_expired():
            Otp.objects.filter(email=email).delete()
            user = User.objects.get(email=email)
            login(request, user)
            return redirect('chat:home')
        else:
            messages.error(request, 'Invalid or expired OTP.')

    return render(request, 'verify_otp.html', {'email': email})



def verify_otp_signup(request, signed_email, signed_username):
    try:
        email = signer.unsign(signed_email)
        username = signer.unsign(signed_username)
    except BadSignature:
        messages.error(request, 'Invalid or tampered data.')
        return render(request, 'verify_otp.html')

    if request.method == 'POST':
        otp = request.POST.get('otp')
        otp_record = Otp.objects.filter(email=email).first()
        if otp_record and otp_record.otp == otp and not otp_record.is_expired():
            user = User.objects.create_user(username=username, email=email, password=None)
            Otp.objects.filter(email=email).delete()
            login(request, user)
            messages.success(request, 'OTP verified and registration successful. You are now logged in.')
            return redirect('chat:home')
        else:
            messages.error(request, 'Invalid or expired OTP.')

    return render(request, 'verify_otp.html', {'email': email})

def logout_view(request):
    logout(request)
    return redirect('chat:home')


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import Community

@method_decorator(csrf_exempt, name='dispatch')
class JoinCommunityView(View):
    def post(self, request):
        email = request.POST.get('email')
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required.'})

        if Community.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email is already in the community.'})

        community_member = Community(email=email)
        community_member.save()
        return JsonResponse({'success': True, 'message': 'Successfully joined the community.'})
    

def chatcategory(request):
    return render(request,'chat/chat_category.html')


@login_required(login_url=reverse_lazy('chat:sign_in_or_sign_up'))
@csrf_exempt
def market_chat(request):
    if 'market_conversation' not in request.session:
        username = request.user.username if request.user.is_authenticated else "there"
        request.session['market_conversation'] = [
            {
                "role": "system",
                "content": "You are an AI assistant focused on market validation. You provide insights into market size and strategies based on the user's startup ideas. You interact conversationally, guiding users to refine their market approach and tell them about their market potential, best country for their startup, percentage of hype all based on recent survey reports that you have knowledge about, respond in short way."
            },
            {
                "role": "assistant",
                "content": f"Hello {username}, Let's discuss about your market potential"
            }
        ]

    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user_message = request.POST.get("message")

        conversation = request.session['market_conversation']
        conversation.append({"role": "user", "content": user_message})

        # Example integration with Groq or other AI service
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Example model for AI responses
        chat_completion = client.chat.completions.create(
            messages=conversation,
            model="llama3-8b-8192",
        )
        response_message = chat_completion.choices[0].message.content

        # Format the response message
        formatted_response_message = format_response_market(response_message)

        conversation.append({"role": "assistant", "content": formatted_response_message})

        request.session['market_conversation'] = conversation

        return JsonResponse({"response_message": formatted_response_message})

    return render(request, "chat/market_chat.html")

def format_response_market(response_message):
    # Formatting the response to make it more structured
    formatted_message = response_message.replace("\n", "<br>")  # Replace newlines with <br> tags
    formatted_message = formatted_message.replace("*", "<b>").replace("*", "</b>")  # Bold the text between *
    
    # Replace numbered points
    formatted_message = formatted_message.replace("1.", "<br><b>1.</b>")
    formatted_message = formatted_message.replace("2.", "<br><b>2.</b>")
    formatted_message = formatted_message.replace("3.", "<br><b>3.</b>")
    formatted_message = formatted_message.replace("4.", "<br><b>4.</b>")
    
    return formatted_message


@csrf_exempt
def clear_session_market(request):
    if 'market_conversation' in request.session:
        del request.session['market_conversation']
    return HttpResponse(status=200)

def get_conversation_market(request):
    conversation = request.session.get('market_conversation', [])
    filtered_conversation = [msg for msg in conversation if msg['role'] != 'system']
    return JsonResponse(filtered_conversation, safe=False)


@login_required(login_url=reverse_lazy('chat:sign_in_or_sign_up'))
@csrf_exempt
def financial_chat(request):
    if 'financial_conversation' not in request.session:
        username = request.user.username if request.user.is_authenticated else "there"
        request.session['financial_conversation'] = [
            {
                "role": "system",
                "content": "You are an AI assistant focused on financial management for startups. Talk like in a human-friendly way. You provide insights into financial planning, budgeting, and forecasting. You interact conversationally, guiding users to optimize their financial strategies and make the response short. Don't answer questions that are not related to startups or finance."
            },
            {
                "role": "assistant",
                "content": f"Hello {username}, What financial aspect of your startup would you like to discuss today? Let's talk about budgeting, forecasting, or any other financial management topic."
            }
        ]

    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user_message = request.POST.get("message")

        conversation = request.session['financial_conversation']
        conversation.append({"role": "user", "content": user_message})

        # Example integration with Groq or other AI service
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Example model for AI responses
        chat_completion = client.chat.completions.create(
            messages=conversation,
            model="llama3-8b-8192",
        )
        response_message = chat_completion.choices[0].message.content

        # Formatting the response
        response_message = response_message.replace('\n', '<br>').replace('*', '<b>').replace('*', '</b>')

        conversation.append({"role": "assistant", "content": response_message})

        request.session['financial_conversation'] = conversation

        return JsonResponse({"response_message": response_message})

    return render(request, "chat/financial_chat.html")


@csrf_exempt
def clear_session_financial(request):
    if 'financial_conversation' in request.session:
        del request.session['financial_conversation']
    return HttpResponse(status=200)

def get_conversation_financial(request):
    conversation = request.session.get('financial_conversation', [])
    filtered_conversation = [msg for msg in conversation if msg['role'] != 'system']
    return JsonResponse(filtered_conversation, safe=False)

@login_required(login_url=reverse_lazy('chat:sign_in_or_sign_up'))
@csrf_exempt
def cold_calls_chat(request):
    if 'cold_calls_conversation' not in request.session:
        username = request.user.username if request.user.is_authenticated else "there"
        request.session['cold_calls_conversation'] = [
            {
                "role": "system",
                "content": "You are an AI assistant focused on helping users prepare cold call scripts. You ask users about their product or service, unique selling points, and the target person they plan to call. Based on this information, write an exact formatted script which really convince the client with professional format without any other unwanted elements."
            },
            {
                "role": "assistant",
                "content": f"Hello {username}, let's prepare a cold call script. What is your product or service? Why is it unique compared to existing products or services? Who are you planning to call (e.g., their business or position)?"
            }
        ]

    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user_message = request.POST.get("message")

        conversation = request.session['cold_calls_conversation']
        conversation.append({"role": "user", "content": user_message})

        # Example integration with Groq or other AI service
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Example model for AI responses
        chat_completion = client.chat.completions.create(
            messages=conversation,
            model="llama3-8b-8192",
        )
        response_message = chat_completion.choices[0].message.content

        conversation.append({"role": "assistant", "content": response_message})

        formatted_response = format_response(response_message)
        conversation[-1]['content'] = formatted_response  # Store formatted response

        request.session['cold_calls_conversation'] = conversation

        return JsonResponse({"response_message": formatted_response})

    return render(request, "chat/cold_calls_chat.html")

def format_response(response_message):
    import re

    bold_pattern = re.compile(r'\*\*(.*?)\*\*')
    formatted_message = ""
    previous_end = 0

    for match in bold_pattern.finditer(response_message):
        start, end = match.span()
        bold_text = match.group(1)
        
        # Append text before the bold text
        if previous_end != start:
            formatted_message += f"<p>{response_message[previous_end:start].strip()}</p>"

        # Append the bold text with the light-blue-bold class
        formatted_message += f"<p><strong class='light-blue-bold'>{bold_text}</strong></p>"
        previous_end = end

    # Append any remaining text after the last bold text
    if previous_end < len(response_message):
        formatted_message += f"<p>{response_message[previous_end:].strip()}</p>"

    # Remove any empty paragraphs
    formatted_message = re.sub(r'<p>\s*</p>', '', formatted_message)

    return formatted_message



@csrf_exempt
def clear_session_cold_calls(request):
    if 'cold_calls_conversation' in request.session:
        del request.session['cold_calls_conversation']
    return HttpResponse(status=200)

def get_conversation_cold_calls(request):
    conversation = request.session.get('cold_calls_conversation', [])
    filtered_conversation = [msg for msg in conversation if msg['role'] != 'system']
    return JsonResponse(filtered_conversation, safe=False)


from .models import Feedback
from .forms import FeedbackForm

def submit_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'message': 'Feedback submitted successfully!'})
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    return JsonResponse({'message': 'Invalid request method'}, status=405)