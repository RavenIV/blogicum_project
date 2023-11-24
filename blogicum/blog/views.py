from datetime import datetime

from django.shortcuts import get_object_or_404, render
from django.views.generic import CreateView
from django.urls import reverse_lazy

from .models import Category, Post
from .forms import PostForm


class PostCreateView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    # Перенаправить на страницу профиля: 
    # success_url = reverse_lazy(')


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
