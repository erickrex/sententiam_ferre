from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    AuthViewSet, GroupViewSet, DecisionViewSet, TaxonomyViewSet, 
    DecisionItemViewSet, VoteViewSet, MessageViewSet, QuestionViewSet, UserAnswerViewSet,
    GenerationViewSet, ExportViewSet
)

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'decisions', DecisionViewSet, basename='decision')
router.register(r'taxonomies', TaxonomyViewSet, basename='taxonomy')
router.register(r'items', DecisionItemViewSet, basename='item')
router.register(r'votes', VoteViewSet, basename='vote')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'answers', UserAnswerViewSet, basename='answer')
router.register(r'generations', GenerationViewSet, basename='generation')
router.register(r'exports', ExportViewSet, basename='export')

urlpatterns = [
    path('', include(router.urls)),
]
