from django.urls import path
from django.views.decorators.http import require_POST
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_donor, name='register_donor'),
    path(
        'registration-success/',
        views.registration_success,
        name='registration_success'
    ),
    path(
    'emergency/create/',
    views.create_emergency_request,
    name='create_emergency_request',
),

    path(
    'emergency/<int:request_id>/',
    views.emergency_request_detail,
    name='emergency_request_detail',
),

   path(
    'emergency/<int:request_id>/select-donors/',
    views.select_donors_for_notification,
    name='select_donors_for_notification',
),

   path(
    'emergency/<int:request_id>/activate/',
    views.update_emergency_status,
    {
        'new_status': 'Active'
    },
    name='activate_emergency_request',
),

  path(
    'emergency/<int:request_id>/fulfill/',
    views.update_emergency_status,
    {
        'new_status': 'Fulfilled'
    },
    name='fulfill_emergency_request',
),

  path(
    'emergency/<int:request_id>/close/',
    views.update_emergency_status,
    {
        'new_status': 'Closed'
    },
    name='close_emergency_request',
),
   path(
    'notifications/',
    views.donor_notifications,
    name='donor_notifications',
),

  path(
    'login/',
    views.user_login,
    name='user_login',
),

 path(
    'notifications/<int:notification_id>/accept/',
    views.donor_response,
    {
        'response_status': 'Accepted'
    },
    name='accept_donor_request',
),

path(
    'notifications/<int:notification_id>/decline/',
    views.donor_response,
    {
        'response_status': 'Declined'
    },
    name='decline_donor_request',
),

path(
    'logout/',
    views.user_logout,
    name='logout',
),

path(
    'password-reset/',
    auth_views.PasswordResetView.as_view(
        template_name='donors/password_reset.html'
    ),
    name='password_reset'
),

path(
    'password-reset/done/',
    auth_views.PasswordResetDoneView.as_view(
        template_name='donors/password_reset_done.html'
    ),
    name='password_reset_done'
),

path(
    'reset/<uidb64>/<token>/',
    auth_views.PasswordResetConfirmView.as_view(
        template_name='donors/password_reset_confirm.html'
    ),
    name='password_reset_confirm'
),

path(
    'reset/done/',
    auth_views.PasswordResetCompleteView.as_view(
        template_name='donors/password_reset_complete.html'
    ),
    name='password_reset_complete'
),

]