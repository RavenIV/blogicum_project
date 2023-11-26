from datetime import datetime
from typing import Any
from django import http

from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
from django.views.generic.list import MultipleObjectMixin
from django.urls import reverse, reverse_lazy

from .models import Category, Post, Comment
from .forms import PostForm, CommentForm


User = get_user_model()

def filter_published_posts(posts):
    return (
        posts.select_related('location', 'category', 'author')
        .filter(
            is_published=True,
            pub_date__lte=datetime.now(),
            category__is_published=True
        )
    )


class IndexView(ListView):
    """Показать ленту опубликованных постов."""
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        return filter_published_posts(Post.objects)


class CategoryDetailView(DetailView, MultipleObjectMixin):
    """Показать опубликованные посты конкретной категории."""
    queryset = Category.objects.filter(is_published=True)
    slug_url_kwarg = 'category_slug'
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        object_list = filter_published_posts(self.get_object().posts)
        return super(CategoryDetailView, self).get_context_data(
            object_list=object_list, **kwargs
        )
    

class PostDetailView(DetailView):
    """Посмотреть конкретную публикацию и комментарии к ней."""
    # model = Post
    queryset = filter_published_posts(Post.objects)
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    # Показать страницу неопубликованного поста его автору.
    # def get_object(self):
    #     if super().get_object().author == self.request.user:
    #         return super().get_object()
    #     return get_object_or_404(
    #         filter_published_posts(Post.objects),
    #         pk=self.kwargs['post_id']
    #     )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создать публикацию."""
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


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Редактировать публикацию, проверив авторство."""
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['post_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', post_id=instance.pk)
        return super().dispatch(request, *args, **kwargs)
    

class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Удалить публикацию, проверив авторство."""
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    
    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(Post, pk=kwargs['post_id'], author=request.user)
        return super().dispatch(request, *args, **kwargs)
    

class ProfileDetailView(DetailView, MultipleObjectMixin):
    """Показать профиль пользователя."""
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'blog/profile.html'
    paginate_by = 10
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        
        if self.get_object() == self.request.user:
            object_list = self.get_object().posts.all()
        else:
            object_list = filter_published_posts(self.get_object().posts)
        
        return super(ProfileDetailView, self).get_context_data(
            object_list=object_list, **kwargs
        )


class UserUpdateView(LoginRequiredMixin, UpdateView):
    """Редактировать данные пользователя."""
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









@login_required
def add_comment(request, pk):
    post = get_object_or_404(filter_published_posts(Post.objects), pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid:
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', pk=pk)