from datetime import datetime
from typing import Any

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

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(Post, pk=kwargs['post_id'], author=request.user)
        return super().dispatch(request, *args, **kwargs)
    

class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Удалить публикацию, проверив авторство."""
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    
    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(Post, pk=kwargs['post_id'], author=request.user)
        return super().dispatch(request, *args, **kwargs)
    

class PostDetailView(DetailView):
    """Посмотреть конкретную публикацию."""
    model = Post
    template_name = 'blog/detail.html'
    
    def get_object(self):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context



def profile(request, username):
    profile = get_object_or_404(User, username=username)

    if profile == request.user:
        posts = profile.posts.all()
    else:
        posts = filter_published_posts(profile.posts)

    return render(request, 'blog/profile.html', {
        'profile': profile,
        'page_obj': Paginator(posts, 10).get_page(
            request.GET.get('page')
        ),
    })


class UserUpdateView(LoginRequiredMixin, UpdateView):
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