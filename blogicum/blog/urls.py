from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('posts/<int:post_id>/edit/', views.PostUpdateView.as_view(), name='edit_post'),
    path('posts/<int:post_id>/delete/', views.PostDeleteView.as_view(), name='delete_post'),
    path('posts/<int:post_id>/', views.PostDetailView.as_view(), name='post_detail'),
    path('posts/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
    path(
        'category/<slug:category_slug>/',
        views.category_posts,
        name='category_posts'
    ),
    path('profile/<username>/', views.profile, name='profile'),
    path('edit_profile/', views.UserUpdateView.as_view(), name='edit_profile'),
    path('', views.index, name='index'),
]
