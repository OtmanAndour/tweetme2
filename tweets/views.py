import random
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.utils.http import is_safe_url

from .forms import TweetForm
from .models import Tweet
from .serializers import TweetSerializer


ALLOWED_HOSTS = settings.ALLOWED_HOSTS

# Create your views here.


def home(request, *args, **kwargs):
    print(request.user or None)
    return render(request, 'pages/home.html', context={}, status=200)


def tweet_create_view(request, *args, **kwargs):
    '''
    REST API create view with Django Rest Framework
    '''
    data = request.POST or None
    serializer = TweetSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
    return JsonResponse({}, status=400)


def tweet_create_view_pure_django(request, *args, **kwargs):
    '''
    Create view with pure Django
    '''
    user = request.user
    if not request.user.is_authenticated:
        user = None
        if request.is_ajax():
            return JsonResponse({}, status=401)
        return redirect(settings.LOGIN_URL)
    form = TweetForm(request.POST or None)
    next_url = request.POST.get("next")
    if form.is_valid():
        obj = form.save(commit=False)
        # do other form related logic
        obj.user = user  # Annon user
        obj.save()
        if request.is_ajax():
            return JsonResponse(obj.serialize(), status=201)
        if (next_url != None and is_safe_url(next_url, ALLOWED_HOSTS)):
            return redirect(next_url)
        form = TweetForm()
    if form.errors:
        if request.is_ajax():
            return JsonResponse(form.errors, status=400)
    return render(request, 'components/form.html', context={"form": form})


def tweet_list_view(request, *args, **kwargs):
    """
    REST API view so it can be consumed by Javascript or React
    Return json data
    """
    query_set = Tweet.objects.all()
    tweets_list = [x.serialize() for x in query_set]
    data = {
        "isUser": False,
        "response": tweets_list
    }
    return JsonResponse(data)


def tweet_details(request, tweet_id, *args, **kwargs):
    """
    REST API view so it can be consumed by Javascript or React
    Return json data
    """
    data = {
        "id": tweet_id,
    }
    status = 200
    try:
        obj = Tweet.objects.get(id=tweet_id)
        data['content'] = obj.content
    except:
        data['message'] = "Not Found"
        status = 404

    # Similar to json.dumps content_type="application/json"
    return JsonResponse(data, status=status)