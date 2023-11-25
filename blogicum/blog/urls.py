from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
    path(
        'category/<slug:category_slug>/',
        views.category_posts,
        name='category_posts'
    ),
    path('profile/<username>/', views.ProfileView.as_view(), name='profile'),
    path('edit_profile/', views.ProfileUpdateView.as_view(), name='edit_profile'),
    path('', views.index, name='index'),
]
