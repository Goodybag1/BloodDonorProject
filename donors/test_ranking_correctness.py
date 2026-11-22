from datetime import date, timedelta

from django.test import TestCase

from .models import Donor
from .matching import rank_donors


class RankingCorrectnessTest(TestCase):

    def create_donor(
        self,
        first_name,
        blood_group,
        city,
        last_donation_date=None,
        gender='Male',
    ):
        return Donor.objects.create(
            first_name=first_name,
            last_name='Test',
            date_of_birth=date(1995, 1, 1),
            gender=gender,
            phone_number=f'09{Donor.objects.count():09d}',
            email=f'{first_name.lower()}@example.com',
            blood_group=blood_group,
            state='Plateau',
            city=city,
            is_available=True,
            is_medically_eligible=True,
            last_donation_date=last_donation_date,
        )

    def test_representative_ranking_order(self):

        # Emergency request:
        # Blood group: AB+
        # Location: Jos, Plateau

        donor_a = self.create_donor(
            first_name='DonorA',
            blood_group='O+',
            city='Jos',
            last_donation_date=date.today() - timedelta(days=270),
        )

        donor_b = self.create_donor(
            first_name='DonorB',
            blood_group='O+',
            city='Bukuru',
            last_donation_date=None,
        )

        donor_c = self.create_donor(
            first_name='DonorC',
            blood_group='O+',
            city='Jos',
            last_donation_date=date.today() - timedelta(days=90),
        )

        donor_d = self.create_donor(
            first_name='DonorD',
            blood_group='A+',
            city='Jos',
            last_donation_date=None,
        )

        ranked = rank_donors(
            Donor.objects.all(),
            'AB+',
            'Plateau',
            'Jos',
        )

        ranked_ids = [
            match['donor'].id
            for match in ranked
        ]

        # Donor D has the same location and readiness as donor B,
        # but is also blood-compatible with AB+.
        self.assertIn(donor_d.id, ranked_ids)

        # Donor B is in the same state but different city.
        self.assertIn(donor_b.id, ranked_ids)

        # Donor A is same city and has been eligible for a long time,
        # so should rank above donor B.
        self.assertLess(
            ranked_ids.index(donor_a.id),
            ranked_ids.index(donor_b.id),
        )

        # Donor C is same city but has only just reached the
        # minimum donation interval, giving it low readiness.
        self.assertLess(
            ranked_ids.index(donor_a.id),
            ranked_ids.index(donor_c.id),
        )

        # Confirm that the different-city donor has lower proximity.
        donor_b_match = next(
            match for match in ranked
            if match['donor'].id == donor_b.id
        )

        self.assertEqual(
            donor_b_match['proximity_score'],
            60
        )

        # Confirm that same-city donors receive maximum proximity.
        donor_a_match = next(
            match for match in ranked
            if match['donor'].id == donor_a.id
        )

        self.assertEqual(
            donor_a_match['proximity_score'],
            100
        )

    def test_incompatible_blood_group_is_excluded(self):

        compatible_donor = self.create_donor(
            first_name='Compatible',
            blood_group='O+',
            city='Jos',
            last_donation_date=None,
        )

        incompatible_donor = self.create_donor(
            first_name='Incompatible',
            blood_group='AB-',
            city='Jos',
            last_donation_date=None,
        )

        ranked = rank_donors(
            Donor.objects.all(),
            'O+',
            'Plateau',
            'Jos',
        )

        ranked_ids = [
            match['donor'].id
            for match in ranked
        ]

        self.assertIn(
            compatible_donor.id,
            ranked_ids
        )

        self.assertNotIn(
            incompatible_donor.id,
            ranked_ids
        )

    
    def test_alternative_weightings(self):

        # Create the same four donors used in the
        # representative ranking test.

        donor_a = self.create_donor(
            first_name='DonorA',
            blood_group='O+',
            city='Jos',
            last_donation_date=date.today() - timedelta(days=270),
        )

        donor_b = self.create_donor(
            first_name='DonorB',
            blood_group='O+',
            city='Bukuru',
            last_donation_date=None,
        )

        donor_c = self.create_donor(
            first_name='DonorC',
            blood_group='O+',
            city='Jos',
            last_donation_date=date.today() - timedelta(days=90),
        )

        donor_d = self.create_donor(
            first_name='DonorD',
            blood_group='A+',
            city='Jos',
            last_donation_date=None,
        )

        donors = [donor_a, donor_b, donor_c, donor_d]

        # Run the existing matching process to obtain
        # the qualifying donors and their score components.

        current_results = rank_donors(
            donors,
            'AB+',
            'Plateau',
            'Jos',
        )

        weightings = {
            '50:50': (0.50, 0.50),
            '60:40': (0.60, 0.40),
            '70:30': (0.70, 0.30),
        }

        ranking_results = {}
        score_results = {}

        for label, (proximity_weight, readiness_weight) in weightings.items():

            recalculated = []

            for match in current_results:

                score = (
                    proximity_weight * match['proximity_score']
                    + readiness_weight * match['readiness_score']
                )

                recalculated.append({
                    'donor': match['donor'],
                    'score': score,
                    'proximity_score': match['proximity_score'],
                    'readiness_score': match['readiness_score'],
                })

            recalculated.sort(
                key=lambda match: (
                    match['score'],
                    match['proximity_score'],
                    match['readiness_score'],
                    -match['donor'].id,
                ),
                reverse=True,
            )

            ranking_results[label] = [
                match['donor'].first_name
                for match in recalculated
            ]

            score_results[label] = {
                match['donor'].first_name: match['score']
                for match in recalculated
            }

        # Verify the expected ranking under each weighting.

        expected_ranking = [
            'DonorA',
            'DonorD',
            'DonorB',
            'DonorC',
        ]

        self.assertEqual(ranking_results['50:50'], expected_ranking)
        self.assertEqual(ranking_results['60:40'], expected_ranking)
        self.assertEqual(ranking_results['70:30'], expected_ranking)

        # Verify the calculated scores.

        self.assertAlmostEqual(
            score_results['50:50']['DonorC'], 51.6667, places=2
        )

        self.assertAlmostEqual(
            score_results['60:40']['DonorC'], 61.3333, places=2
        )

        self.assertAlmostEqual(
            score_results['70:30']['DonorC'], 71.0, places=2
        )

        self.assertEqual(
            score_results['50:50']['DonorB'], 80
        )

        self.assertEqual(
            score_results['60:40']['DonorB'], 76
        )

        self.assertEqual(
            score_results['70:30']['DonorB'], 72
        )
    

    def test_different_state_is_excluded(self):

        same_state = self.create_donor(
            first_name='SameState',
            blood_group='O+',
            city='Jos',
            last_donation_date=None,
        )

        different_state = Donor.objects.create(
            first_name='DifferentState',
            last_name='Test',
            date_of_birth=date(1995, 1, 1),
            gender='Male',
            phone_number=f'09{Donor.objects.count():09d}',
            email='differentstate@example.com',
            blood_group='O+',
            state='Lagos',
            city='Lagos',
            is_available=True,
            is_medically_eligible=True,
            last_donation_date=None,
        )

        ranked = rank_donors(
            Donor.objects.all(),
            'O+',
            'Plateau',
            'Jos',
        )

        ranked_ids = [
            match['donor'].id
            for match in ranked
        ]

        self.assertIn(
            same_state.id,
            ranked_ids
        )

        self.assertNotIn(
            different_state.id,
            ranked_ids
        )
 
        