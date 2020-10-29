import random
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.utils.http import is_safe_url

from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from ..forms import TweetForm
from ..models import Tweet
from ..serializers import (
    TweetSerializer, TweetActionSerializer, TweetCreateSerializer)


ALLOWED_HOSTS = settings.ALLOWED_HOSTS

"""
    REST API views with Django Rest Framework
"""


@api_view(["POST"])  # http method the client sends must be a post
# @authentication_classes([SessionAuthentication, MyCustomAuth])
@permission_classes([IsAuthenticated])
def tweet_create_view(request, *args, **kwargs):
    serializer = TweetCreateSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response({}, status=400)

def get_paginated_queryset_response(query_set, request):
    paginator = PageNumberPagination()
    paginator.page_size = 20
    paginated_qs = paginator.paginate_queryset(query_set, request)
    serializer = TweetSerializer(paginated_qs, many=True, context={"request":request})
    return paginator.get_paginated_response(serializer.data) #Response(serializer.data, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tweet_feed_view(request, *args, **kwargs):
    user = request.user
    qs = Tweet.objects.feed(user)
    return get_paginated_queryset_response(qs, request)

@api_view(["GET"])
def tweet_list_view(request, *args, **kwargs):
    query_set = Tweet.objects.all()
    username = request.GET.get('username') # ? username=otman
    if username != None :
        query_set = query_set.filter(user__username__iexact=username)
    return get_paginated_queryset_response(query_set, request)


@api_view(["GET"])
def tweet_details(request, tweet_id, *args, **kwargs):
    query_set = Tweet.objects.filter(id=tweet_id)
    if not query_set.exists():
        return Response({}, status=404)
    obj = query_set.first()
    serializer = TweetSerializer(obj)
    return Response(serializer.data, status=200)


@api_view(["DELETE", "POST"])
@permission_classes([IsAuthenticated])
def tweet_delete_view(request, tweet_id, *args, **kwargs):
    query_set = Tweet.objects.filter(id=tweet_id)
    if not query_set.exists():
        return Response({}, status=404)
    query_set = query_set.filter(user=request.user)
    if not query_set.exists():
        return Response({"message": "You cannot delete this tweet"}, status=401)
    obj = query_set.first()
    obj.delete()
    return Response({"message": "Tweet removed"}, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def tweet_action_view(request, *args, **kwargs):
    """
    id is required
    Actions options are: like, unlike retweet
    """
    serializer = TweetActionSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        data = serializer.validated_data
        tweet_id = data.get("id")
        action = data.get("action")
        query_set = Tweet.objects.filter(id=tweet_id)
        if not query_set.exists():
            return Response({}, status=404)
        obj = query_set.first()
        if action == "like":
            obj.likes.add(request.user)
            serializer = TweetSerializer(obj)
            return Response(serializer.data, status=200)
        elif action == "unlike":
            obj.likes.remove(request.user)
            serializer = TweetSerializer(obj)
            return Response(serializer.data, status=200)
        elif action == "retweet":
            new_tweet = Tweet.objects.create(
                user=request.user, parent=obj, content=obj.content,)
            serializer = TweetSerializer(new_tweet)
            return Response(serializer.data, status=201)
    return Response({}, status=200)


"""
    Views with pure Django
"""


def tweet_create_view_pure_django(request, *args, **kwargs):

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
        obj.user = user
        obj.save()
        if request.is_ajax():
            return JsonResponse(obj.serialize(), status=201)
        if next_url != None and is_safe_url(next_url, ALLOWED_HOSTS):
            return redirect(next_url)
        form = TweetForm()
    if form.errors:
        if request.is_ajax():
            return JsonResponse(form.errors, status=400)
    return render(request, "components/form.html", context={"form": form})


def tweet_list_view_pure_django(request, *args, **kwargs):
    """
    REST API view so it can be consumed by Javascript or React
    Return json data
    """
    query_set = Tweet.objects.all()
    tweets_list = [x.serialize() for x in query_set]
    data = {"isUser": False, "response": tweets_list}
    return JsonResponse(data)


def tweet_details_pure_django(request, tweet_id, *args, **kwargs):
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
        data["content"] = obj.content
    except:
        data["message"] = "Not Found"
        status = 404

    # Similar to json.dumps content_type="application/json"
    return JsonResponse(data, status=status)
