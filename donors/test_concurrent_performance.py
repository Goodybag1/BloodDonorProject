
import time
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.contrib.auth.models import User
from django.db import close_old_connections
from django.test import TransactionTestCase
from django.urls import reverse

from .models import Donor, EmergencyBloodRequest


class ConcurrentEmergencyMatchingTest(TransactionTestCase):

    CONCURRENT_USERS = 5
    RUNS = 3
    DONOR_COUNT = 1000

    def setUp(self):
        self.staff_users = []

        for i in range(self.CONCURRENT_USERS):
            user = User.objects.create_user(
                username=f'concurrent_admin_{i}',
                password='Performance123!',
                is_staff=True
            )
            self.staff_users.append(user)

        self.emergency_request = EmergencyBloodRequest.objects.create(
            created_by=self.staff_users[0],
            requested_blood_group='AB+',
            state='Plateau',
            city='Jos',
            request_details='Concurrent performance test.',
            status='Active',
        )

        donors = []

        for i in range(self.DONOR_COUNT):
            donors.append(
                Donor(
                    first_name=f'Test{i}',
                    last_name='Donor',
                    date_of_birth=date(1995, 1, 1),
                    gender='Male',
                    phone_number=f'090{i:08d}',
                    email=f'concurrent{i}@example.com',
                    blood_group='O+',
                    state='Plateau',
                    city='Jos',
                    is_available=True,
                    is_medically_eligible=True,
                    last_donation_date=None,
                )
            )

        Donor.objects.bulk_create(donors)

    def make_request(self, user_id, url, barrier):
        close_old_connections()

        try:
            user = User.objects.get(pk=user_id)

            from django.test import Client
            client = Client()
            client.force_login(user)

            # Wait until all five clients are ready.
            barrier.wait(timeout=30)

            start_time = time.perf_counter()
            response = client.get(url)
            end_time = time.perf_counter()

            return response.status_code, (
                end_time - start_time
            ) * 1000

        finally:
            close_old_connections()

    def test_concurrent_emergency_matching(self):

        url = reverse(
            'emergency_request_detail',
            args=[self.emergency_request.id]
        )

        all_timings = []

        print('\n')
        print('=' * 70)
        print('CONCURRENT EMERGENCY MATCHING PERFORMANCE TEST')
        print(f'Donors: {self.DONOR_COUNT}')
        print(f'Concurrent users: {self.CONCURRENT_USERS}')
        print(f'Concurrent runs: {self.RUNS}')
        print('=' * 70)

        for run_number in range(1, self.RUNS + 1):

            barrier = Barrier(self.CONCURRENT_USERS)

            with ThreadPoolExecutor(
                max_workers=self.CONCURRENT_USERS
            ) as executor:

                futures = [
                    executor.submit(
                        self.make_request,
                        user.id,
                        url,
                        barrier
                    )
                    for user in self.staff_users
                ]

                results = [
                    future.result(timeout=60)
                    for future in futures
                ]

            for status_code, elapsed_ms in results:
                self.assertEqual(status_code, 200)
                all_timings.append(elapsed_ms)

            print(
                f'Run {run_number}: '
                f'{len(results)} concurrent requests completed.'
            )

        average_time = sum(all_timings) / len(all_timings)

        print('-' * 70)
        print(f'Total successful requests: {len(all_timings)}')
        print(f'Average response time: {average_time:.2f} ms')
        print(f'Minimum response time: {min(all_timings):.2f} ms')
        print(f'Maximum response time: {max(all_timings):.2f} ms')
        print('=' * 70)
