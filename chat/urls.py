from django.urls import path
from .views import *

app_name = 'chat'

urlpatterns = [
    path('', home, name='home'),
    path('chat-category/',chatcategory,name='chatcategory'),

    path('chat/', chat_view, name='chat_view'),
    path('clear_session/', clear_session, name='clear_session'),
    path('get_conversation/', get_conversation, name='get_conversation'),

    path('market_chat/', market_chat, name='market_chat'),
    path('clear_session_market/', clear_session_market, name='clear_session_market'),
    path('get_conversation_market/', get_conversation_market, name='clear_session_market'),

    path('financial_chat/', financial_chat, name='financial_chat'),
    path('clear_session_financial/', clear_session_financial, name='clear_session_financial'),
    path('get_conversation_financial/', get_conversation_financial, name='get_conversation_financial'),

    path('cold_calls_chat/', cold_calls_chat, name='cold_calls_chat'),
    path('clear_session_cold_calls/', clear_session_cold_calls, name='clear_session_cold_calls'),
    path('get_conversation_cold_calls/', get_conversation_cold_calls, name='get_conversation_cold_calls'),

    path('submit_feedback/',submit_feedback, name='submit_feedback'),
    

    path('interview/', interview_view, name='interview_view'),
    path('clear-interview-context/', clear_interview_context_view, name='clear_interview_context'),


    path('about/', about, name='about'),
    
    path('contact/', contact, name='contact'),
    path('contact-form/', ContactFormView.as_view(), name='contact_form'),
    

    path('login/', sign_in_or_sign_up, name='sign_in_or_sign_up'),
    path('verify-otp/<str:signed_email>/',verify_otp, name='verify_otp'),
    path('verify-otp-signup/<str:signed_email>/<str:signed_username>/',verify_otp_signup, name='verify_otp_signup'),
    path('logout/', logout_view, name='logout'),

    path('join-community/', JoinCommunityView.as_view(), name='join_community'),

]
