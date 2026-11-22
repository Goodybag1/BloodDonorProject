from django.contrib import admin
from .models import (
    Donor,
    EmergencyBloodRequest,
    DonorResponse,
    Notification,
)


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'first_name',
        'last_name',
        'gender',
        'date_of_birth',
        'phone_number',
        'email',
        'city',
        'state',
        'blood_group',
        'date_registered',
        'last_donation_date',
        'is_available',
        'is_medically_eligible',
        'last_updated',
    )
    
    list_display_links = ('first_name', 'last_name')


@admin.register(EmergencyBloodRequest)
class EmergencyBloodRequestAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'requested_blood_group',
        'state',
        'city',
        'status',
        'created_by',
        'date_created',
    )


@admin.register(DonorResponse)
class DonorResponseAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'donor',
        'request',
        'response_status',
        'response_date',
    )

    list_display_links = (
        'donor',
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
    'donor',
    'request',
    'message',
    'is_read',
    'date_created',
)
    list_filter = (
        'is_read',
        'date_created',
    )

    search_fields = (
        'donor__first_name',
        'donor__last_name',
        'message',
    )    