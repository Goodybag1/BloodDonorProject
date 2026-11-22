import time
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Donor, EmergencyBloodRequest, Notification, DonorResponse


class DonorResponsePerformanceTest(TestCase):

    DONOR_COUNTS = [50, 100, 250, 500, 1000]
    RUNS_PER_SIZE = 5

    @classmethod
    def setUpTestData(cls):
        cls.staff_user = User.objects.create_user(
            username='response_admin',
            password='Response123!'
        )

        cls.staff_user.is_staff = True
        cls.staff_user.save()

        cls.donor_user = User.objects.create_user(
            username='response_donor',
            password='ResponseDonor123!'
        )

        cls.donor = Donor.objects.create(
            user=cls.donor_user,
            first_name='Response',
            last_name='Donor',
            date_of_birth=date(1995, 1, 1),
            gender='Male',
            phone_number='09100000001',
            email='response@example.com',
            blood_group='O+',
            state='Plateau',
            city='Jos',
            is_available=True,
            is_medically_eligible=True,
            last_donation_date=None,
        )

        cls.emergency_request = EmergencyBloodRequest.objects.create(
            created_by=cls.staff_user,
            requested_blood_group='AB+',
            state='Plateau',
            city='Jos',
            request_details='Response performance test.',
            status='Active',
        )

    def create_test_donors(self, count):
        donors = []

        # The response donor already exists.
        remaining = count - 1

        for i in range(remaining):
            donors.append(
                Donor(
                    first_name=f'Test{i}',
                    last_name='Donor',
                    date_of_birth=date(1995, 1, 1),
                    gender='Male',
                    phone_number=f'092{i:08d}',
                    email=f'response{i}@example.com',
                    blood_group='O+',
                    state='Plateau',
                    city='Jos',
                    is_available=True,
                    is_medically_eligible=True,
                    last_donation_date=None,
                )
            )

        if donors:
            Donor.objects.bulk_create(donors)

    def test_donor_response_performance(self):

        self.client.login(
            username='response_donor',
            password='ResponseDonor123!'
        )

        print('\n')
        print('=' * 70)
        print('DONOR RESPONSE PERFORMANCE TEST')
        print('=' * 70)

        for donor_count in self.DONOR_COUNTS:

            Donor.objects.exclude(
                id=self.donor.id
            ).delete()

            Notification.objects.all().delete()
            DonorResponse.objects.all().delete()

            self.create_test_donors(donor_count)

            notification = Notification.objects.create(
                donor=self.donor,
                request=self.emergency_request,
                message='Emergency blood donation request.'
            )

            url = reverse(
                'accept_donor_request',
                args=[notification.id]
            )

            # Warm-up request
            self.client.post(url)

            DonorResponse.objects.all().delete()

            timings = []

            for _ in range(self.RUNS_PER_SIZE):

                DonorResponse.objects.all().delete()

                start_time = time.perf_counter()

                response = self.client.post(url)

                end_time = time.perf_counter()

                elapsed_ms = (
                    end_time - start_time
                ) * 1000

                timings.append(elapsed_ms)

                self.assertEqual(
                    response.status_code,
                    302
                )

                self.assertTrue(
                    DonorResponse.objects.filter(
                        donor=self.donor,
                        request=self.emergency_request,
                        response_status='Accepted'
                    ).exists()
                )

            average_time = (
                sum(timings) / len(timings)
            )

            print(
                f'{donor_count:>5} donors | '
                f'Runs: {self.RUNS_PER_SIZE} | '
                f'Average: {average_time:.2f} ms | '
                f'Min: {min(timings):.2f} ms | '
                f'Max: {max(timings):.2f} ms'
            )

        print('=' * 70)
        print()