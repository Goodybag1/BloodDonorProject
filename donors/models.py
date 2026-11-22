from django.db import models
from django.contrib.auth.models import User


class Donor(models.Model):

    BLOOD_GROUPS = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donor_profile'
    )

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    date_of_birth = models.DateField()

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )

    phone_number = models.CharField(max_length=15, unique=True)

    email = models.EmailField(unique=True)

    blood_group = models.CharField(
        max_length=3,
        choices=BLOOD_GROUPS
    )

    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    is_available = models.BooleanField(default=True)

    is_medically_eligible = models.BooleanField(default=True)

    last_donation_date = models.DateField(
        null=True,
        blank=True
    )

    date_registered = models.DateTimeField(auto_now_add=True)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.blood_group})"


class EmergencyBloodRequest(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Active', 'Active'),
        ('Fulfilled', 'Fulfilled'),
        ('Closed', 'Closed'),
    ]

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='emergency_requests'
    )

    requested_blood_group = models.CharField(
        max_length=3,
        choices=Donor.BLOOD_GROUPS
    )

    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    request_details = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.requested_blood_group} emergency request - {self.city}"


class DonorResponse(models.Model):

    RESPONSE_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Declined', 'Declined'),
    ]

    donor = models.ForeignKey(
        Donor,
        on_delete=models.CASCADE,
        related_name='responses'
    )

    request = models.ForeignKey(
        EmergencyBloodRequest,
        on_delete=models.CASCADE,
        related_name='responses'
    )

    response_status = models.CharField(
        max_length=10,
        choices=RESPONSE_CHOICES,
        default='Pending'
    )

    response_date = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['donor', 'request'],
                name='unique_donor_request_response'
            )
        ]

    def __str__(self):
        return f"{self.donor} - {self.request} - {self.response_status}"
    
class Notification(models.Model):

    donor = models.ForeignKey(
        Donor,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    request = models.ForeignKey(
        EmergencyBloodRequest,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    date_created = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"Notification for "
            f"{self.donor.first_name} "
            f"{self.donor.last_name}"
        )    