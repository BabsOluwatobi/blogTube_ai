from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from pytube import YouTube
from django.conf import Settings
import os
import assemblyai as aai
import openai
# Create your views here.
# AUTHENTICATION

@login_required
def index(request):
    return render(request, 'index.html')

def user_login(request):
    if request.method == 'POST':
        username= request.POST['username']
        password=request.POST['password']

        user= authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect ('/')
        else:
            error_message='invalid login credentials'
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username= request.POST['username']
        email=request.POST['email']
        password=request.POST['password']
        repeatPassword=request.POST['repeatPassword']
       
        if password==repeatPassword:
            try:
                user= User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'error creating account'
                return render(request, 'signup.html', {'error_message' : error_message})
        else:
            error_message= 'Password do not match'
            return render(request, 'signup.html', {'error_message' : error_message})
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')


# BLOG GENERATION
@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data= json.loads(request.body)
            yt_link = data['link']
            # return JsonResponse({'content:yt_link'})
        except(KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'invalid data sent'}, status = 400)
            
            
    # youtube title
        title = yt_title(yt_link)

     # get transcription
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error': "failed to get transcription"}, status=500)
    
    # openai
        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': "failed to get transcription"}, status=500)
    # return blog as response
        return JsonResponse({'content': blog_content})    

    else: 
        return JsonResponse({'error': 'invalid request method'}, status = 405)
        




# get title _ using pytube
def yt_title(link):
     yt= YouTube(link)
     title = yt.title
     return title

# download audio file
def download_audio(link):
    yt=YouTube(link)
    video =yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=Settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)
    return new_file

#transcript
def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key= "60fbe201970747ccb6e49338fc586fa7"
    
    transcriber= aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    return transcript.text

def generate_blog_from_transcription(transcription):
    openai.api_key ="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"

    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"
    response = openai.completions.create(
        model= "text-davinci-003",
        prompt=prompt,
        max_tokens=1000
    )
    generated_content = response.choices[0].text.strip()
    return generated_content