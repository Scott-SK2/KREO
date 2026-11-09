from django.urls import path

from . import views

urlpatterns = [
    path("reports", views.ReportCreateView.as_view(), name="reports"),
    path("blocks", views.BlockView.as_view(), name="blocks"),
    path("blocks/<int:block_id>", views.BlockDetailView.as_view(), name="block-detail"),
    path("appeals", views.AppealView.as_view(), name="appeals"),
    path(
        "me/moderation-decisions", views.MyModerationDecisionsView.as_view(), name="me-moderation"
    ),
    path("admin/reports", views.AdminReportListView.as_view(), name="admin-reports"),
    path(
        "admin/reports/<uuid:report_id>/actions",
        views.AdminReportActionView.as_view(),
        name="admin-report-actions",
    ),
    path("admin/appeals", views.AdminAppealListView.as_view(), name="admin-appeals"),
    path(
        "admin/appeals/<uuid:appeal_id>/decide",
        views.AdminAppealDecideView.as_view(),
        name="admin-appeal-decide",
    ),
    path("admin/audit", views.AdminAuditView.as_view(), name="admin-audit"),
    path(
        "admin/users/<uuid:user_id>/actions",
        views.AdminUserStatusView.as_view(),
        name="admin-user-actions",
    ),
]
