from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('posts/create/', views.PostCreateView.as_view(), name='create'),
    path(
        'category/<slug:category_slug>/',
        views.category_posts,
        name='category_posts'
    ),
    path('', views.index, name='index'),
]
