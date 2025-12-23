from django.views.generic import ListView, DetailView
from .models import Post

class NewsListView(ListView):
    model = Post
    template_name = 'news/list.html'
    context_object_name = 'posts'
    queryset = Post.objects.filter(is_active=True)

class NewsDetailView(DetailView):
    model = Post
    template_name = 'news/detail.html'
    context_object_name = 'post'