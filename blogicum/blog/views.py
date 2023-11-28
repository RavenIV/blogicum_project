from datetime import datetime

from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.urls import reverse, reverse_lazy

from .forms import PostForm, CommentForm
from .models import Category, Post, Comment, User


PAGINATE_BY = 10


def filter_published_posts(posts):
    return (
        posts.select_related('location', 'category', 'author')
        .filter(
            is_published=True,
            pub_date__lte=datetime.now(),
            category__is_published=True
        ).annotate(comment_count=Count('comments'))
    )


class PostsListMixin(ListView):
    model = Post
    ordering = ('-pub_date',)
    paginate_by = PAGINATE_BY


class IndexView(PostsListMixin):
    """Показать ленту опубликованных постов."""

    template_name = 'blog/index.html'
    queryset = filter_published_posts(Post.objects)


class CategoryView(PostsListMixin):
    """Показать опубликованные посты конкретной категории."""

    template_name = 'blog/category.html'

    def get_object(self):
        return get_object_or_404(
            Category,
            is_published=True,
            slug=self.kwargs.get('category_slug')
        )

    def get_queryset(self):
        self.queryset = filter_published_posts(self.get_object().posts)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        return dict(
            {'category': self.get_object()},
            **super().get_context_data(**kwargs)
        )


class ProfileView(PostsListMixin):
    """
    Показать профиль автора и его опубликованные посты.
    Если это страница пользователя, показать все его посты.
    """

    template_name = 'blog/profile.html'

    def get_object(self):
        return get_object_or_404(
            User, username=self.kwargs.get('username')
        )

    def get_queryset(self):
        profile = self.get_object()
        if profile == self.request.user:
            self.queryset = profile.posts.select_related(
                'category', 'location'
            ).annotate(comment_count=Count('comments'))
        else:
            self.queryset = filter_published_posts(profile.posts)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        return dict(
            {'profile': self.get_object()},
            **super().get_context_data(**kwargs)
        )


class PostDetailView(DetailView):
    """Посмотреть конкретную публикацию и комментарии к ней."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        post = super().get_object()
        if post.author == self.request.user:
            return post
        return get_object_or_404(
            filter_published_posts(Post.objects),
            pk=self.kwargs[self.pk_url_kwarg]
        )

    def get_context_data(self, **kwargs):
        return dict({
            'form': CommentForm(),
            'comments': self.get_object().comments.select_related('author')
        }, **super().get_context_data(**kwargs))


class PostEditMixin(LoginRequiredMixin):
    model = Post
    template_name = 'blog/create.html'


class PostFormMixin(PostEditMixin):
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostValidAuthorMixin:
    """
    Если пользователь - не автор,
    перенаправить на страницу публикации.
    """

    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['post_id'])
        if instance.author != request.user:
            return redirect(instance)
        return super().dispatch(request, *args, **kwargs)


class PostCreateView(PostFormMixin, CreateView):
    """Создать публикацию."""

    def get_success_url(self):
        return reverse('blog:profile', kwargs={
            'username': self.request.user.username
        })


class PostUpdateView(PostFormMixin, PostValidAuthorMixin, UpdateView):
    """Редактировать публикацию."""


class PostDeleteView(PostEditMixin, PostValidAuthorMixin, DeleteView):
    """Удалить публикацию."""

    success_url = reverse_lazy('blog:index')


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


class BaseCommentMixin(LoginRequiredMixin):
    model = Comment

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={
            'post_id': self.kwargs.get('post_id')
        })


class ValidCommentMixin(BaseCommentMixin):
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_object(self):
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post__pk=self.kwargs['post_id'],
            author=self.request.user
        )


class CommentCreateView(BaseCommentMixin, CreateView):
    """Написать комментарий к публикации."""

    template_name = 'blog/detail.html'
    fields = ('text',)
    post_to_comment = None

    def dispatch(self, request, *args, **kwargs):
        self.post_to_comment = get_object_or_404(
            filter_published_posts(Post.objects),
            pk=self.kwargs.get('post_id')
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_to_comment
        return super().form_valid(form)


class CommentUpdateView(ValidCommentMixin, UpdateView):
    """Редактировать комментарий к публикации."""

    fields = ('text',)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.get_object().post
        return super().form_valid(form)


class CommentDeleteView(ValidCommentMixin, DeleteView):
    """Удалить комментарий к публикации."""
