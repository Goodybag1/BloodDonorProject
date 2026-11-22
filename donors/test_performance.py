import time
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Donor, EmergencyBloodRequest


class EmergencyMatchingPerformanceTest(TestCase):

    DONOR_COUNTS = [50, 100, 250, 500, 1000]
    RUNS_PER_SIZE = 5

    @classmethod
    def setUpTestData(cls):
        cls.staff_user = User.objects.create_user(
            username='performance_admin',
            password='Performance123!'
        )

        cls.staff_user.is_staff = True
        cls.staff_user.save()

        cls.emergency_request = EmergencyBloodRequest.objects.create(
            created_by=cls.staff_user,
            requested_blood_group='AB+',
            state='Plateau',
            city='Jos',
            request_details='Performance testing emergency request.',
            status='Active',
        )

    def create_test_donors(self, count):
        donors = []

        for i in range(count):
            donors.append(
                Donor(
                    first_name=f'Test{i}',
                    last_name='Donor',
                    date_of_birth=date(1995, 1, 1),
                    gender='Male',
                    phone_number=f'090{i:08d}',
                    email=f'performance{i}@example.com',
                    blood_group='O+',
                    state='Plateau',
                    city='Jos',
                    is_available=True,
                    is_medically_eligible=True,
                    last_donation_date=None,
                )
            )

        Donor.objects.bulk_create(donors)

    def test_emergency_matching_performance(self):

        self.client.login(
            username='performance_admin',
            password='Performance123!'
        )

        print('\n')
        print('=' * 70)
        print('EMERGENCY MATCHING PERFORMANCE TEST')
        print('=' * 70)

        for donor_count in self.DONOR_COUNTS:

            # Remove donors from the previous test size.
            Donor.objects.all().delete()

            # Create the required number of test donors.
            self.create_test_donors(donor_count)

            url = reverse(
                'emergency_request_detail',
                args=[self.emergency_request.id]
            )

            # Warm-up request.
            self.client.get(url)

            timings = []

            for _ in range(self.RUNS_PER_SIZE):

                start_time = time.perf_counter()

                response = self.client.get(url)

                end_time = time.perf_counter()

                elapsed_ms = (
                    end_time - start_time
                ) * 1000

                timings.append(elapsed_ms)

                self.assertEqual(
                    response.status_code,
                    200
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