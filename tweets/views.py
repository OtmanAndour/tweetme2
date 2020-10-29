from django.conf import settings
from django.shortcuts import render
ALLOWED_HOSTS = settings.ALLOWED_HOSTS

# Create your views here.


def home_view(request, *args, **kwargs):
    return render(request, "pages/feed.html")

def tweets_list_view(request, *args, **kwargs):
    return render(request, "tweets/list.html")

def tweets_detail_view(request, tweet_id, *args, **kwargs):
    return render(request, "tweets/detail.html", context={"tweet_id":tweet_id})
