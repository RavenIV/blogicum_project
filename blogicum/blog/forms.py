from django import forms
from django.forms import ModelChoiceField

from .models import Post, Comment


class LocationChoiceField(ModelChoiceField):

    def label_from_instance(self, object):
        return f'{object.name}'


class CategoryChoiceField(ModelChoiceField):

    def label_from_instance(self, object):
        return f'{object.title}'


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ('author',)
        field_classes = {
            'location': LocationChoiceField,
            'category': CategoryChoiceField,
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
