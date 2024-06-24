from django.urls import path
from .views import *

app_name = 'chat'

urlpatterns = [
    path('', home, name='home'),
    path('chat/', chat_view, name='chat_view'),
    path('clear_session/', clear_session, name='clear_session'),
    path('get_conversation/', get_conversation, name='get_conversation'),
    path('interview/', interview_view, name='interview_view'),

    path('about/', about, name='about'),
    
    path('contact/', contact, name='contact'),
    path('contact-form/', ContactFormView.as_view(), name='contact_form'),
    

    path('login/', sign_in_or_sign_up, name='sign_in_or_sign_up'),
    path('verify-otp/<str:signed_email>/',verify_otp, name='verify_otp'),
    path('verify-otp-signup/<str:signed_email>/<str:signed_username>/',verify_otp_signup, name='verify_otp_signup'),
    path('logout/', logout_view, name='logout'),

    path('join-community/', JoinCommunityView.as_view(), name='join_community'),

]
