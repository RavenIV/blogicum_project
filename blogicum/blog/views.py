from datetime import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
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


class ValidPostsMixin:
    queryset = Post.objects.prefetch_related(
        'location', 'category', 'author'
    )

    def get_queryset(self):
        self.queryset = self.queryset.filter(
            is_published=True,
            pub_date__lte=datetime.now(),
            category__is_published=True
        )
        return super().get_queryset()
    


class IndexView(ValidPostsMixin, ListView):
    """Показать ленту опубликованных постов."""

    template_name = 'blog/index.html'
    paginate_by = 10

class CategoryView(ValidPostsMixin, ListView):
    """Показать опубликованные посты конкретной категории."""

    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(
            category__slug=self.kwargs.get('category_slug')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category, 
            is_published=True, 
            slug=self.kwargs.get('category_slug')
        )
        return context
    

class ProfileView(ValidPostsMixin, ListView):
    """
    Показать профиль автора и его опубликованные посты.
    Если это страница пользователя, показать все его посты.
    """

    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        profile = get_object_or_404(
            User, username=self.kwargs.get('username')
        )
        if profile == self.request.user:
            return User.objects.get(username=profile.username).posts.select_related('category', 'location')
        else:
            queryset = super().get_queryset()
            return queryset.filter(author__username=profile.username)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(User, username=self.kwargs.get('username'))
        return context


class PostDetailView(ValidPostsMixin, DetailView):
    """Посмотреть конкретную публикацию и комментарии к ней."""

    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

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
    """
    Редактировать публикацию. Если пользователь - не автор, 
    перенаправить на страницу публикации.
    """

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