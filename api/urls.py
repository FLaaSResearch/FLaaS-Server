from django.urls import path
from rest_framework_simplejwt import views as jwt_views

from api.views import ProjectList, ProjectDetail, GetSamples, ReportAvailibility, GetModel, JoinRound, SubmitModel, SubmitResults, ComputePerformance

urlpatterns = [

    # Samples
    path('get-samples/<str:dataset_type>/<str:app>/', GetSamples.as_view(), name='get-samples'),

    # Project
    path('project/', ProjectList.as_view(), name='project-list'),
    path('project/<int:project_id>/', ProjectDetail.as_view(), name='project-details'),
    path('project/<int:project_id>/get-model/<str:round>/', GetModel.as_view(), name='get-model'),
    path('project/<int:project_id>/join-round/<str:round>/', JoinRound.as_view(), name='join-round'),

    # Reporting
    path('report-availability', ReportAvailibility.as_view(), name='report-availability'),
    path('project/<int:project_id>/submit-results/<str:round>/<str:filename>', SubmitResults.as_view(), name='submit-results'),
    path('project/<int:project_id>/submit-model/<str:round>/<str:filename>', SubmitModel.as_view(), name='submit-model'),

    # JWT Tokens
    path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    # path('token/verify/', jwt_views.TokenVerifyView.as_view(), name='token_verify'),
]
