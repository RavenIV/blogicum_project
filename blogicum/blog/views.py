from datetime import datetime
from typing import Any
from django import http

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import CreateView, TemplateView, UpdateView
from django.urls import reverse

from .models import Category, Post
from .forms import PostForm
from users.forms import CustomUserCreationForm


User = get_user_model()


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('blog:profile', kwargs={
            'username': self.request.user
        })
    

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'blog/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User, 
            username=self.request.user
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ('username', 'first_name', 'last_name', 'email')
    template_name = 'blog/user.html'

    def get_object(self):
        return User.objects.get(username=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(User, username=request.user)
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('blog:profile', kwargs={
            'username': self.request.user
        })



def filter_published_posts(posts):
    return (
        posts.select_related('location', 'category', 'author')
        .filter(
            is_published=True,
            pub_date__lte=datetime.now(),
            category__is_published=True
        )
    )


def index(request):
    return render(request, 'blog/index.html', {
        'post_list': filter_published_posts(Post.objects)[:5]
    })


def post_detail(request, post_id):
    return render(request, 'blog/detail.html', {
        'post': get_object_or_404(
            filter_published_posts(Post.objects),
            pk=post_id,
        )
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        is_published=True,
        slug=category_slug
    )
    return render(request, 'blog/category.html', {
        'category': category,
        'post_list': filter_published_posts(category.posts)
    })
