from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.db import IntegrityError, transaction

from .models import (
    Donor,
    DonorResponse,
    EmergencyBloodRequest,
    Notification,
)


class EmergencyRequestWorkflowTests(TestCase):

    def setUp(self):
        """
        Create a staff user for testing protected
        emergency-request functionality.
        """

        self.staff_user = User.objects.create_user(
            username='testadmin',
            password='TestAdmin123!'
        )

        self.staff_user.is_staff = True
        self.staff_user.save()

        self.client.login(
            username='testadmin',
            password='TestAdmin123!'
        )


    def test_staff_user_can_access_emergency_creation_page(self):
        """
        A logged-in staff user should be able to access
        the emergency request creation page.
        """

        response = self.client.get(
            '/emergency/create/'
        )

        self.assertEqual(
            response.status_code,
            200
        )


    def test_staff_user_can_create_emergency_request(self):
        """
        A staff user should be able to submit a valid
        emergency blood request.
        """

        response = self.client.post(
            '/emergency/create/',
            {
                'requested_blood_group': 'AB+',
                'state': 'Plateau',
                'city': 'Jos',
                'request_details': (
                    'Emergency blood requirement for testing.'
                ),
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertEqual(
            EmergencyBloodRequest.objects.count(),
            1
        )

        emergency_request = (
            EmergencyBloodRequest.objects.first()
        )

        self.assertEqual(
            emergency_request.requested_blood_group,
            'AB+'
        )

        self.assertEqual(
            emergency_request.state,
            'Plateau'
        )

        self.assertEqual(
            emergency_request.city,
            'Jos'
        )

        self.assertEqual(
            emergency_request.status,
            'Pending'
        )

        self.assertEqual(
            emergency_request.created_by,
            self.staff_user
        )


    def test_unauthenticated_user_cannot_create_emergency_request(self):
        """
        An unauthenticated user should be redirected to
        the login page.
        """

        self.client.logout()

        response = self.client.get(
            '/emergency/create/'
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertIn(
            '/login/',
            response.url
        )


    def test_non_staff_user_cannot_create_emergency_request(self):
        """
        A normal authenticated user should not be allowed
        to access the emergency request creation page.
        """

        self.client.logout()

        normal_user = User.objects.create_user(
            username='normaluser',
            password='NormalUser123!'
        )

        self.client.login(
            username='normaluser',
            password='NormalUser123!'
        )

        response = self.client.get(
            '/emergency/create/'
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertIn(
            '/',
            response.url
        )


    def create_emergency_request(self):
        """
        Create a test emergency request in the default
        Pending state.
        """

        return EmergencyBloodRequest.objects.create(
            created_by=self.staff_user,
            requested_blood_group='AB+',
            state='Plateau',
            city='Jos',
            request_details='Test emergency request.'
        )


    def test_pending_request_can_be_activated(self):
        """
        A Pending emergency request should be able
        to transition to Active.
        """

        emergency_request = self.create_emergency_request()

        response = self.client.post(
            f'/emergency/{emergency_request.id}/activate/'
        )

        self.assertEqual(
            response.status_code,
            302
        )

        emergency_request.refresh_from_db()

        self.assertEqual(
            emergency_request.status,
            'Active'
        )


    def test_active_request_can_be_fulfilled(self):
        """
        An Active emergency request should be able
        to transition to Fulfilled.
        """

        emergency_request = self.create_emergency_request()

        emergency_request.status = 'Active'
        emergency_request.save()

        response = self.client.post(
            f'/emergency/{emergency_request.id}/fulfill/'
        )

        self.assertEqual(
            response.status_code,
            302
        )

        emergency_request.refresh_from_db()

        self.assertEqual(
            emergency_request.status,
            'Fulfilled'
        )


    def test_fulfilled_request_can_be_closed(self):
        """
        A Fulfilled emergency request should be able
        to transition to Closed.
        """

        emergency_request = self.create_emergency_request()

        emergency_request.status = 'Fulfilled'
        emergency_request.save()

        response = self.client.post(
            f'/emergency/{emergency_request.id}/close/'
        )

        self.assertEqual(
            response.status_code,
            302
        )

        emergency_request.refresh_from_db()

        self.assertEqual(
            emergency_request.status,
            'Closed'
        )


    def test_invalid_status_transition_is_rejected(self):
        """
        A Pending request should not be able to jump
        directly to Fulfilled.
        """

        emergency_request = self.create_emergency_request()

        response = self.client.post(
            f'/emergency/{emergency_request.id}/fulfill/'
        )

        self.assertEqual(
            response.status_code,
            302
        )

        emergency_request.refresh_from_db()

        self.assertEqual(
            emergency_request.status,
            'Pending'
        )


    def create_test_donor(self):
        """
        Create a donor linked to a normal user account.
        """

        donor_user = User.objects.create_user(
            username='testdonor',
            password='TestDonor123!'
        )

        donor = Donor.objects.create(
            user=donor_user,
            first_name='Test',
            last_name='Donor',
            date_of_birth=(
                date.today()
                - timedelta(days=30 * 365)
            ),
            gender='Male',
            phone_number='08012345678',
            email='testdonor@example.com',
            blood_group='O+',
            state='Plateau',
            city='Jos',
            is_available=True,
            is_medically_eligible=True,
            last_donation_date=None,
        )

        return donor, donor_user


    def test_selected_donor_receives_notification(self):
        """
        Selecting a valid matching donor should create
        both a DonorResponse and a Notification.
        """

        donor, donor_user = self.create_test_donor()

        emergency_request = self.create_emergency_request()
        emergency_request.status = 'Active'
        emergency_request.save()

        response = self.client.post(
            reverse(
                'select_donors_for_notification',
                args=[emergency_request.id]
            ),
            {
                'selected_donors': [str(donor.id)]
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertTrue(
            DonorResponse.objects.filter(
                donor=donor,
                request=emergency_request
            ).exists()
        )

        self.assertTrue(
            Notification.objects.filter(
                donor=donor,
                request=emergency_request
            ).exists()
        )


    def test_notification_is_created_with_pending_response(self):
        """
        A newly notified donor should have a Pending
        DonorResponse.
        """

        donor, donor_user = self.create_test_donor()

        emergency_request = self.create_emergency_request()
        emergency_request.status = 'Active'
        emergency_request.save()

        self.client.post(
            reverse(
                'select_donors_for_notification',
                args=[emergency_request.id]
            ),
            {
                'selected_donors': [str(donor.id)]
            }
        )

        donor_response = DonorResponse.objects.get(
            donor=donor,
            request=emergency_request
        )

        self.assertEqual(
            donor_response.response_status,
            'Pending'
        )


    def test_duplicate_donor_request_response_is_rejected(self):
        """
        A donor should not have more than one response
        record for the same emergency request.
        """

        donor, donor_user = self.create_test_donor()
        emergency_request = self.create_emergency_request()

        # Create the first donor-request response.
        DonorResponse.objects.create(
            donor=donor,
            request=emergency_request,
            response_status='Pending'
        )

        # Attempt to create a duplicate response.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DonorResponse.objects.create(
                    donor=donor,
                    request=emergency_request,
                    response_status='Pending'
                )

        # Confirm that only one response record exists.
        self.assertEqual(
            DonorResponse.objects.filter(
                donor=donor,
                request=emergency_request
            ).count(),
            1
        )


    def test_donor_can_view_own_notifications(self):
        """
        A donor linked to a donor profile should be able
        to access their notification page.
        """

        donor, donor_user = self.create_test_donor()

        emergency_request = self.create_emergency_request()

        Notification.objects.create(
            donor=donor,
            request=emergency_request,
            message='Test emergency notification.'
        )

        self.client.logout()

        self.client.login(
            username='testdonor',
            password='TestDonor123!'
        )

        response = self.client.get(
            reverse('donor_notifications')
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            'Test emergency notification.'
        )


    def test_donor_can_accept_notification(self):
        """
        A donor should be able to accept their own
        emergency notification.
        """

        donor, donor_user = self.create_test_donor()

        emergency_request = self.create_emergency_request()
        emergency_request.status = 'Active'
        emergency_request.save()

        notification = Notification.objects.create(
            donor=donor,
            request=emergency_request,
            message='Test emergency notification.'
        )

        self.client.logout()

        self.client.login(
            username='testdonor',
            password='TestDonor123!'
        )

        response = self.client.post(
            reverse(
                'accept_donor_request',
                args=[notification.id]
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        donor_response = DonorResponse.objects.get(
            donor=donor,
            request=emergency_request
        )

        self.assertEqual(
            donor_response.response_status,
            'Accepted'
        )

        self.assertIsNotNone(
            donor_response.response_date
        )


    def test_donor_can_decline_notification(self):
        """
        A donor should be able to decline their own
        emergency notification.
        """

        donor, donor_user = self.create_test_donor()

        emergency_request = self.create_emergency_request()
        emergency_request.status = 'Active'
        emergency_request.save()

        notification = Notification.objects.create(
            donor=donor,
            request=emergency_request,
            message='Test emergency notification.'
        )

        self.client.logout()

        self.client.login(
            username='testdonor',
            password='TestDonor123!'
        )

        response = self.client.post(
            reverse(
                'decline_donor_request',
                args=[notification.id]
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        donor_response = DonorResponse.objects.get(
            donor=donor,
            request=emergency_request
        )

        self.assertEqual(
            donor_response.response_status,
            'Declined'
        )

        self.assertIsNotNone(
            donor_response.response_date
        )


    def test_donor_cannot_respond_to_another_donors_notification(self):
        """
        A donor must not be able to accept or decline
        another donor's notification.
        """

        donor_one, donor_one_user = self.create_test_donor()

        donor_two_user = User.objects.create_user(
            username='testdonor2',
            password='TestDonor456!'
        )

        donor_two = Donor.objects.create(
            user=donor_two_user,
            first_name='Second',
            last_name='Donor',
            date_of_birth=(
                date.today()
                - timedelta(days=30 * 365)
            ),
            gender='Male',
            phone_number='08087654321',
            email='testdonor2@example.com',
            blood_group='O+',
            state='Plateau',
            city='Jos',
            is_available=True,
            is_medically_eligible=True,
            last_donation_date=None,
        )

        emergency_request = self.create_emergency_request()

        notification = Notification.objects.create(
            donor=donor_two,
            request=emergency_request,
            message='Private notification for donor two.'
        )

        self.client.logout()

        self.client.login(
            username='testdonor',
            password='TestDonor123!'
        )

        response = self.client.post(
            reverse(
                'accept_donor_request',
                args=[notification.id]
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )

        self.assertFalse(
            DonorResponse.objects.filter(
                donor=donor_one,
                request=emergency_request
            ).exists()
        )


    def test_non_staff_user_cannot_view_emergency_request(self):
        """
        A normal authenticated user should not be able
        to view an emergency request.
        """

        emergency_request = self.create_emergency_request()

        self.client.logout()

        normal_user = User.objects.create_user(
            username='viewer',
            password='Viewer123!'
        )

        self.client.login(
            username='viewer',
            password='Viewer123!'
        )

        response = self.client.get(
            reverse(
                'emergency_request_detail',
                args=[emergency_request.id]
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertIn(
            '/',
            response.url
        )


    def test_unauthenticated_user_cannot_view_emergency_request(self):
        """
        An unauthenticated user should be redirected to
        the login page when attempting to view an emergency request.
        """

        emergency_request = self.create_emergency_request()

        self.client.logout()

        response = self.client.get(
            reverse(
                'emergency_request_detail',
                args=[emergency_request.id]
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertIn(
            '/login/',
            response.url
        )


    def test_non_staff_user_cannot_select_donors(self):
        """
        A normal authenticated user should not be able
        to select donors for notification.
        """

        emergency_request = self.create_emergency_request()

        self.client.logout()

        normal_user = User.objects.create_user(
            username='selector',
            password='Selector123!'
        )

        self.client.login(
            username='selector',
            password='Selector123!'
        )

        response = self.client.post(
            reverse(
                'select_donors_for_notification',
                args=[emergency_request.id]
            ),
            {
                'selected_donors': []
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertIn(
            '/',
            response.url
        )


    def test_unauthenticated_user_cannot_select_donors(self):
        """
        An unauthenticated user should not be able
        to select donors for notification.
        """

        emergency_request = self.create_emergency_request()

        self.client.logout()

        response = self.client.post(
            reverse(
                'select_donors_for_notification',
                args=[emergency_request.id]
            ),
            {
                'selected_donors': []
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertIn(
            '/login/',
            response.url
        )


    def test_closed_request_cannot_generate_notifications(self):
        """
        A closed emergency request must not generate
        new donor notifications.
        """

        donor, donor_user = self.create_test_donor()

        emergency_request = self.create_emergency_request()

        emergency_request.status = 'Closed'
        emergency_request.save()

        response = self.client.post(
            reverse(
                'select_donors_for_notification',
                args=[emergency_request.id]
            ),
            {
                'selected_donors': [str(donor.id)]
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            Notification.objects.filter(
                donor=donor,
                request=emergency_request
            ).exists()
        )

        self.assertFalse(
            DonorResponse.objects.filter(
                donor=donor,
                request=emergency_request
            ).exists()
        )


    def test_non_matching_donor_cannot_be_manually_selected(self):
        """
        A donor who does not satisfy the matching engine
        criteria must not receive a notification even if
        their ID is manually submitted.
        """

        # This donor is in a different state and therefore
        # should be rejected by the proximity filter.
        donor, donor_user = self.create_test_donor()

        donor.state = 'Kaduna'
        donor.city = 'Kaduna'
        donor.save()

        emergency_request = self.create_emergency_request()

        response = self.client.post(
            reverse(
                'select_donors_for_notification',
                args=[emergency_request.id]
            ),
            {
                'selected_donors': [str(donor.id)]
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            Notification.objects.filter(
                donor=donor,
                request=emergency_request
            ).exists()
        )

        self.assertFalse(
            DonorResponse.objects.filter(
                donor=donor,
                request=emergency_request
            ).exists()
        )