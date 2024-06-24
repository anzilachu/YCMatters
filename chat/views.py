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
        request.session['conversation'] = [
            {"role": "system", "content": "You are an AI assistant knowledgeable about Y Combinator. You hold all the information from Y Combinator's YouTube channel and understand Y Combinator's ideology, so talk like you are exactly like a human from y combinator, dont give any data or information which is not from the y combinator yt channel"}
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
        user_message = request.POST.get("message")
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

        context = request.session.get('conversation_context', [
            {"role": "system", "content": "You are a Y Combinator interviewer, based on all data of how the yc interview works you can ask questions and be polite"}
        ])
        

        context.append({"role": "user", "content": user_message})
        
        chat_completion = client.chat.completions.create(
            messages=context,
            model="llama3-8b-8192",
        )
        response_message = chat_completion.choices[0].message.content
        
        context.append({"role": "assistant", "content": response_message})
        
        request.session['conversation_context'] = context
        
        return JsonResponse({"response_message": response_message})
    
    return render(request, "chat/interview_chat.html")


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
                messages.info(request, 'OTP sent to your email.')
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
            messages.success(request, 'OTP verified. You are now logged in.')
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