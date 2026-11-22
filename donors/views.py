from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from django.contrib.auth import (
    authenticate,
    login,
    logout,
    get_user_model,
)

from django.contrib.auth.decorators import (
    login_required,
    user_passes_test,
)

from django.db import transaction
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import (
    DonorRegistrationForm,
    EmergencyBloodRequestForm,
)

from .models import (
    Donor,
    EmergencyBloodRequest,
    DonorResponse,
    Notification,
)

from .matching import rank_donors


def is_staff_user(user):
    return user.is_staff


def home(request):
    return render(request, 'donors/home.html')


@transaction.atomic
def register_donor(request):

    if request.method == 'POST':
        form = DonorRegistrationForm(request.POST)

        if form.is_valid():
            User = get_user_model()

            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
            )

            donor = form.save(commit=False)
            donor.user = user
            donor.save()

            return redirect('registration_success')

    else:
        form = DonorRegistrationForm()

    return render(
        request,
        'donors/register.html',
        {'form': form}
    )
def register_test(request):
    form = DonorRegistrationForm()

    return render(
        request,
        'donors/register_test.html',
        {'form': form}
    )

def registration_success(request):
    return render(request, 'donors/registration_success.html')

@login_required
@user_passes_test(
    is_staff_user,
    login_url='home'
)
def create_emergency_request(request):

    if request.method == 'POST':
        form = EmergencyBloodRequestForm(request.POST)

        if form.is_valid():
            emergency_request = form.save(commit=False)
            emergency_request.created_by = request.user
            emergency_request.save()

            return redirect(
                'emergency_request_detail',
                request_id=emergency_request.id
            )

    else:
        form = EmergencyBloodRequestForm()

    return render(
        request,
        'donors/emergency_request.html',
        {'form': form}
    )


@login_required
@user_passes_test(
    is_staff_user,
    login_url='home'
)
def emergency_request_detail(request, request_id):

    emergency_request = get_object_or_404(
        EmergencyBloodRequest,
        id=request_id
    )

    donors = Donor.objects.all()

    ranked_donors = rank_donors(
        donors,
        emergency_request.requested_blood_group,
        emergency_request.state,
        emergency_request.city,
    )

    donor_responses = DonorResponse.objects.filter(
        request=emergency_request
    ).select_related('donor').order_by(
        'donor__first_name',
        'donor__last_name'
    )

    return render(
        request,
        'donors/emergency_request_detail.html',
        {
            'emergency_request': emergency_request,
            'ranked_donors': ranked_donors,
            'donor_responses': donor_responses,
        }
    )


@login_required
@user_passes_test(
    is_staff_user,
    login_url='home'
)
def select_donors_for_notification(request, request_id):

    emergency_request = get_object_or_404(
        EmergencyBloodRequest,
        id=request_id
    )

    # Only active requests can be used to notify donors.
    if emergency_request.status != 'Active':
        return redirect(
        'emergency_request_detail',
        request_id=emergency_request.id
        )

    if request.method == 'POST':

        selected_donor_ids = request.POST.getlist(
            'selected_donors'
        )

        # Recalculate the ranked matches from the
        # current donor data.
        ranked_donors = rank_donors(
            Donor.objects.all(),
            emergency_request.requested_blood_group,
            emergency_request.state,
            emergency_request.city,
        )

        # Only donors currently returned by the
        # matching engine are considered valid.
        valid_donor_ids = {
            match['donor'].id
            for match in ranked_donors
        }

        # Keep only selected donors that are valid
        # matching donors.
        valid_selected_ids = [
            donor_id
            for donor_id in selected_donor_ids
            if donor_id.isdigit()
            and int(donor_id) in valid_donor_ids
        ]

        donors = Donor.objects.filter(
            id__in=valid_selected_ids
        )

        for donor in donors:

            DonorResponse.objects.get_or_create(
                donor=donor,
                request=emergency_request,
                defaults={
                    'response_status': 'Pending'
                }
            )

            Notification.objects.get_or_create(
                donor=donor,
                request=emergency_request,
                defaults={
                    'message': (
                        f'Urgent blood request: '
                        f'{emergency_request.requested_blood_group} '
                        f'blood is required in '
                        f'{emergency_request.city}, '
                        f'{emergency_request.state}. '
                        f'Please respond to this emergency request.'
                    )
                }
            )

        return redirect(
            'emergency_request_detail',
            request_id=emergency_request.id
        )

    return redirect(
        'emergency_request_detail',
        request_id=emergency_request.id
    )


@login_required
def donor_notifications(request):

    donor = Donor.objects.filter(
        user=request.user
    ).first()

    if donor is None:
        return redirect('home')

    notifications = Notification.objects.filter(
        donor=donor
    ).order_by('-date_created')

    # Mark unread notifications as read when viewed.
    notifications.filter(is_read=False).update(
        is_read=True
    )

    for notification in notifications:

        response = DonorResponse.objects.filter(
            donor=donor,
            request=notification.request
        ).first()

        notification.donor_response = response

    return render(
        request,
        'donors/donor_notifications.html',
        {'notifications': notifications}
    )


def user_login(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            next_url = request.GET.get('next')

            # Redirect only to an allowed destination.
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect('home')

        return render(
            request,
            'donors/login.html',
            {
                'error': 'Invalid username or password.'
            }
        )

    return render(
        request,
        'donors/login.html'
    )
@login_required
@require_POST
def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def donor_response(request, notification_id, response_status):

    donor = Donor.objects.filter(
        user=request.user
    ).first()

    # Only users linked to a donor profile can respond
    # to emergency notifications.
    if donor is None:
        return redirect('home')

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        donor=donor
    )

    # Donors can respond only while the emergency request
    # is active.
    if notification.request.status != 'Active':
        return redirect('donor_notifications')

    if request.method == 'POST':

        donor_response, created = DonorResponse.objects.get_or_create(
            donor=donor,
            request=notification.request,
            defaults={
                'response_status': response_status,
            }
        )

        if not created:
            donor_response.response_status = response_status

        donor_response.response_date = timezone.now()
        donor_response.save()

    return redirect('donor_notifications')

@login_required
@user_passes_test(
    is_staff_user,
    login_url='home'
)
def update_emergency_status(request, request_id, new_status):

    emergency_request = get_object_or_404(
        EmergencyBloodRequest,
        id=request_id
    )

    allowed_transitions = {
        'Pending': ['Active'],
        'Active': ['Fulfilled'],
        'Fulfilled': ['Closed'],
    }

    current_status = emergency_request.status

    if request.method == 'POST':

        if new_status in allowed_transitions.get(
            current_status,
            []
        ):
            emergency_request.status = new_status
            emergency_request.save()

    return redirect(
        'emergency_request_detail',
        request_id=emergency_request.id
    )

def home_test(request):
    return render(request, 'donors/home_test.html')    