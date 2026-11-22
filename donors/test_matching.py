from datetime import date, timedelta

from django.test import SimpleTestCase, TestCase

from .matching import (
    is_blood_compatible,
    calculate_location_score,
    calculate_proximity_score,
    calculate_readiness_score,
    calculate_weighted_score,
    filter_mandatory_criteria,
    filter_by_proximity,
    calculate_match_score,
    rank_donors,
)
from .models import Donor


class MatchingScoreTests(SimpleTestCase):

    def test_o_negative_is_compatible_with_ab_positive(self):
        self.assertTrue(
            is_blood_compatible('O-', 'AB+')
        )


    def test_ab_positive_is_not_compatible_with_o_negative(self):
        self.assertFalse(
            is_blood_compatible('AB+', 'O-')
        )


    def test_a_positive_is_compatible_with_ab_positive(self):
        self.assertTrue(
            is_blood_compatible('A+', 'AB+')
        )


    def test_same_city_location_score(self):
        result = calculate_location_score(
            'Plateau',
            'Jos',
            'Plateau',
            'Jos'
        )

        self.assertEqual(result, 2)


    def test_same_state_different_city_location_score(self):
        result = calculate_location_score(
            'Plateau',
            'Barkin Ladi',
            'Plateau',
            'Jos'
        )

        self.assertEqual(result, 1)


    def test_different_state_location_score(self):
        result = calculate_location_score(
            'Kaduna',
            'Kaduna',
            'Plateau',
            'Jos'
        )

        self.assertEqual(result, 0)


    def test_proximity_score_same_city(self):
        self.assertEqual(
            calculate_proximity_score(2),
            100
        )


    def test_proximity_score_same_state(self):
        self.assertEqual(
            calculate_proximity_score(1),
            60
        )


    def test_proximity_score_different_state(self):
        self.assertEqual(
            calculate_proximity_score(0),
            0
        )


    def test_readiness_score_without_previous_donation(self):
        result = calculate_readiness_score(
            'Male',
            None
        )

        self.assertEqual(result, 100)


    def test_readiness_score_at_minimum_interval(self):
        last_donation_date = (
            date.today() - timedelta(weeks=12)
        )

        result = calculate_readiness_score(
            'Male',
            last_donation_date
        )

        self.assertEqual(result, 0)


    def test_readiness_score_30_days_beyond_minimum(self):
        last_donation_date = (
            date.today()
            - timedelta(weeks=12)
            - timedelta(days=30)
        )

        result = calculate_readiness_score(
            'Male',
            last_donation_date
        )

        self.assertAlmostEqual(
            result,
            16.6666666667,
            places=5
        )


    def test_readiness_score_is_capped_at_100(self):
        last_donation_date = (
            date.today() - timedelta(days=500)
        )

        result = calculate_readiness_score(
            'Male',
            last_donation_date
        )

        self.assertEqual(result, 100)


    def test_weighted_score(self):
        result = calculate_weighted_score(
            100,
            50
        )

        self.assertEqual(result, 80)


    def test_weighted_score_all_proximity(self):
        result = calculate_weighted_score(
            100,
            0
        )

        self.assertEqual(result, 60)


    def test_weighted_score_all_readiness(self):
        result = calculate_weighted_score(
            0,
            100
        )

        self.assertEqual(result, 40)


class MatchingFilterTests(TestCase):

    def create_donor(
        self,
        first_name='Test',
        last_name='Donor',
        blood_group='O+',
        city='Jos',
        state='Plateau',
        is_available=True,
        is_medically_eligible=True,
        last_donation_date=None,
    ):
        return Donor.objects.create(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=(
                date.today()
                - timedelta(days=30 * 365)
            ),
            gender='Male',
            phone_number=f'080{Donor.objects.count():08d}',
            email=(
                f'test{Donor.objects.count()}'
                '@example.com'
            ),
            blood_group=blood_group,
            state=state,
            city=city,
            is_available=is_available,
            is_medically_eligible=is_medically_eligible,
            last_donation_date=last_donation_date,
        )


    def test_mandatory_filter_accepts_valid_donor(self):
        donor = self.create_donor(
            blood_group='O+'
        )

        result = filter_mandatory_criteria(
            donor,
            'AB+'
        )

        self.assertTrue(result)


    def test_mandatory_filter_rejects_incompatible_blood(self):
        donor = self.create_donor(
            blood_group='AB+'
        )

        result = filter_mandatory_criteria(
            donor,
            'O-'
        )

        self.assertFalse(result)


    def test_mandatory_filter_rejects_unavailable_donor(self):
        donor = self.create_donor(
            blood_group='O+',
            is_available=False
        )

        result = filter_mandatory_criteria(
            donor,
            'AB+'
        )

        self.assertFalse(result)


    def test_mandatory_filter_rejects_medically_ineligible_donor(self):
        donor = self.create_donor(
            blood_group='O+',
            is_medically_eligible=False
        )

        result = filter_mandatory_criteria(
            donor,
            'AB+'
        )

        self.assertFalse(result)


    def test_proximity_filter_accepts_same_city(self):
        donor = self.create_donor(
            city='Jos',
            state='Plateau'
        )

        result = filter_by_proximity(
            donor,
            'Plateau',
            'Jos'
        )

        self.assertTrue(result)


    def test_proximity_filter_accepts_same_state(self):
        donor = self.create_donor(
            city='Barkin Ladi',
            state='Plateau'
        )

        result = filter_by_proximity(
            donor,
            'Plateau',
            'Jos'
        )

        self.assertTrue(result)


    def test_proximity_filter_rejects_different_state(self):
        donor = self.create_donor(
            city='Kaduna',
            state='Kaduna'
        )

        result = filter_by_proximity(
            donor,
            'Plateau',
            'Jos'
        )

        self.assertFalse(result)


class CompleteMatchingTests(TestCase):

    def create_donor(
        self,
        first_name,
        last_name,
        blood_group='O+',
        city='Jos',
        state='Plateau',
        last_donation_date=None,
    ):
        return Donor.objects.create(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=(
                date.today()
                - timedelta(days=30 * 365)
            ),
            gender='Male',
            phone_number=f'081{Donor.objects.count():08d}',
            email=(
                f'match{Donor.objects.count()}'
                '@example.com'
            ),
            blood_group=blood_group,
            state=state,
            city=city,
            is_available=True,
            is_medically_eligible=True,
            last_donation_date=last_donation_date,
        )


    def test_complete_match_returns_score_for_valid_donor(self):
        donor = self.create_donor(
            first_name='Michael',
            last_name='Adamu'
        )

        result = calculate_match_score(
            donor,
            'AB+',
            'Plateau',
            'Jos'
        )

        self.assertIsNotNone(result)

        self.assertEqual(
            result['proximity_score'],
            100
        )

        self.assertEqual(
            result['readiness_score'],
            100
        )

        self.assertEqual(
            result['final_score'],
            100
        )


    def test_complete_match_rejects_wrong_blood_group(self):
        donor = self.create_donor(
            first_name='Wrong',
            last_name='Blood',
            blood_group='AB+'
        )

        result = calculate_match_score(
            donor,
            'O-',
            'Plateau',
            'Jos'
        )

        self.assertIsNone(result)


    def test_complete_match_rejects_different_state(self):
        donor = self.create_donor(
            first_name='Different',
            last_name='State',
            state='Kaduna',
            city='Kaduna'
        )

        result = calculate_match_score(
            donor,
            'AB+',
            'Plateau',
            'Jos'
        )

        self.assertIsNone(result)


    def test_complete_match_calculates_weighted_score(self):
        last_donation_date = (
            date.today()
            - timedelta(weeks=12)
            - timedelta(days=90)
        )

        donor = self.create_donor(
            first_name='Scored',
            last_name='Donor',
            last_donation_date=last_donation_date
        )

        result = calculate_match_score(
            donor,
            'AB+',
            'Plateau',
            'Jos'
        )

        self.assertIsNotNone(result)

        self.assertEqual(
            result['proximity_score'],
            100
        )

        self.assertAlmostEqual(
            result['readiness_score'],
            50,
            places=2
        )

        self.assertAlmostEqual(
            result['final_score'],
            80,
            places=2
        )


    def test_rank_donors_orders_highest_score_first(self):
        high_score_donor = self.create_donor(
            first_name='High',
            last_name='Score',
            city='Jos',
            state='Plateau',
            last_donation_date=None
        )

        lower_score_donor = self.create_donor(
            first_name='Lower',
            last_name='Score',
            city='Barkin Ladi',
            state='Plateau',
            last_donation_date=None
        )

        ranked = rank_donors(
            Donor.objects.all(),
            'AB+',
            'Plateau',
            'Jos'
        )

        self.assertEqual(
            len(ranked),
            2
        )

        self.assertEqual(
            ranked[0]['donor'].id,
            high_score_donor.id
        )

        self.assertEqual(
            ranked[1]['donor'].id,
            lower_score_donor.id
        )

        self.assertEqual(
            ranked[0]['proximity_score'],
            100
        )

        self.assertEqual(
            ranked[1]['proximity_score'],
            60
        )
        
    def test_rank_donors_uses_donor_id_as_final_tie_breaker(self):
        first_donor = self.create_donor(
            first_name='First',
            last_name='Tie',
            city='Jos',
            state='Plateau',
            last_donation_date=None,
        )

        second_donor = self.create_donor(
            first_name='Second',
            last_name='Tie',
            city='Jos',
            state='Plateau',
            last_donation_date=None,
        )

        ranked = rank_donors(
            Donor.objects.all(),
            'AB+',
            'Plateau',
            'Jos'
        )

        self.assertEqual(len(ranked), 2)

        self.assertEqual(
            ranked[0]['donor'].id,
            first_donor.id
        )

        self.assertEqual(
            ranked[1]['donor'].id,
            second_donor.id
        )