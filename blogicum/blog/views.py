from datetime import datetime
from typing import Any

from django.db.models import Count
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
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
    model = Post
    ordering = ('-pub_date',)

    def get_queryset(self):
        self.queryset = filter_published_posts(
            Post.objects
        ).annotate(comment_count=Count('comments'))
        return super().get_queryset()
    


class IndexView(ValidPostsMixin, ListView):
    """Показать ленту опубликованных постов."""

    template_name = 'blog/index.html'
    paginate_by = 10


class CategoryView(ValidPostsMixin, ListView):
    """Показать опубликованные посты конкретной категории."""

    template_name = 'blog/category.html'
    paginate_by = 10
    category = None

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category, 
            is_published=True, 
            slug=self.kwargs.get('category_slug')
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(
            category__slug=self.category.slug
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context
    

class ProfileView(ValidPostsMixin, ListView):
    """
    Показать профиль автора и его опубликованные посты.
    Если это страница пользователя, показать все его посты.
    """

    profile = None
    template_name = 'blog/profile.html'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(
            User, username=self.kwargs.get('username')
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.profile == self.request.user:
            return User.objects.get(
                username=self.profile.username
            ).posts.select_related('category', 'location')
        else:
            queryset = super().get_queryset()
            return queryset.filter(author__username=self.profile.username)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
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
            return redirect(instance)
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
        return get_object_or_404(User, username=self.request.user)
    
    def get_success_url(self):
        return reverse('blog:profile', kwargs={
            'username': self.request.user
        })


class CommentMixin(LoginRequiredMixin):
    model = Comment
    post_to_comment = None

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        self.post_to_comment = get_object_or_404(
            filter_published_posts(Post.objects),
            pk=self.kwargs.get('post_id')
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={
            'post_id': self.post_to_comment.pk
        })
    

class CommentFormValidMixin(CommentMixin):
    fields = ('text',)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_to_comment
        return super().form_valid(form)


class CommentCreateView(CommentFormValidMixin, CreateView):
    """Написать комментарий к публикации."""

    template_name = 'blog/detail.html'


class CommentUpdateView(CommentFormValidMixin, UpdateView):
    """Редактировать комментарий к публикации."""
    
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(Comment, pk=kwargs['comment_id'], author=request.user)
        return super().dispatch(request, *args, **kwargs)


class CommentDeleteView(CommentMixin, DeleteView):
    """Удалить комментарий к публикации."""

    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(Comment, pk=kwargs['comment_id'], author=request.user)
        return super().dispatch(request, *args, **kwargs)