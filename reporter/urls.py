from django.urls import path
from .views import ProjectDetail, create_report, ProjectEdit, ProjectAdd, ProjectList, delete_link, ProjectDelete, share_link

urlpatterns = [
    path('', ProjectList.as_view(), name='project_list'),
    path('edit/<int:pk>/', ProjectEdit.as_view(), name='project_edit'),
    path('report/', create_report, name='create_report'),
    path('add/', ProjectAdd.as_view(), name='project_add'),
    path('<int:pk>/', ProjectDetail.as_view(), name='project_detail'),
    path('delete-link/<int:pk>/', delete_link, name='delete_link'),
    path('share-link/', share_link, name='share_link'),
    path('<int:pk>/delete/', ProjectDelete.as_view(), name='project_delete'),
]