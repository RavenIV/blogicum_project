from datetime import datetime

from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView
from django.urls import reverse

from .models import Category, Post
from .forms import PostForm


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


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(User, username=request.user)
        return super().dispatch(request, *args, **kwargs)
    

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
