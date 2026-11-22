from datetime import date, timedelta

from django.test import SimpleTestCase

from .eligibility import (
    calculate_age,
    is_age_eligible,
    get_minimum_donation_interval,
    is_donation_interval_eligible,
    is_system_eligible,
)


class EligibilityEngineTests(SimpleTestCase):

    def test_calculate_age(self):
        """
        The age calculation should return the
        correct completed age.
        """

        today = date.today()

        date_of_birth = date(
            today.year - 30,
            today.month,
            today.day
        )

        self.assertEqual(
            calculate_age(date_of_birth),
            30
        )


    def test_age_18_is_eligible(self):
        """
        A donor who is exactly 18 years old
        should be eligible.
        """

        today = date.today()

        date_of_birth = date(
            today.year - 18,
            today.month,
            today.day
        )

        self.assertTrue(
            is_age_eligible(date_of_birth)
        )


    def test_age_65_is_eligible(self):
        """
        A donor who is exactly 65 years old
        should be eligible.
        """

        today = date.today()

        date_of_birth = date(
            today.year - 65,
            today.month,
            today.day
        )

        self.assertTrue(
            is_age_eligible(date_of_birth)
        )


    def test_under_18_is_not_eligible(self):
        """
        A donor below 18 years old should not
        be eligible.
        """

        today = date.today()

        date_of_birth = date(
            today.year - 17,
            today.month,
            today.day
        )

        self.assertFalse(
            is_age_eligible(date_of_birth)
        )


    def test_over_65_is_not_eligible(self):
        """
        A donor above 65 years old should not
        be eligible.
        """

        today = date.today()

        date_of_birth = date(
            today.year - 66,
            today.month,
            today.day
        )

        self.assertFalse(
            is_age_eligible(date_of_birth)
        )


    def test_male_minimum_donation_interval(self):
        """
        Male donors should have a minimum interval
        of 12 weeks.
        """

        interval = get_minimum_donation_interval(
            'Male'
        )

        self.assertEqual(
            interval,
            timedelta(weeks=12)
        )


    def test_female_minimum_donation_interval(self):
        """
        Female donors should have a minimum interval
        of 16 weeks.
        """

        interval = get_minimum_donation_interval(
            'Female'
        )

        self.assertEqual(
            interval,
            timedelta(weeks=16)
        )


    def test_male_after_12_weeks_is_eligible(self):
        """
        A male donor who has waited exactly
        12 weeks should be eligible.
        """

        last_donation_date = (
            date.today() - timedelta(weeks=12)
        )

        self.assertTrue(
            is_donation_interval_eligible(
                last_donation_date,
                'Male'
            )
        )


    def test_male_before_12_weeks_is_not_eligible(self):
        """
        A male donor who has waited less than
        12 weeks should not be eligible.
        """

        last_donation_date = (
            date.today() - timedelta(days=83)
        )

        self.assertFalse(
            is_donation_interval_eligible(
                last_donation_date,
                'Male'
            )
        )


    def test_female_after_16_weeks_is_eligible(self):
        """
        A female donor who has waited exactly
        16 weeks should be eligible.
        """

        last_donation_date = (
            date.today() - timedelta(weeks=16)
        )

        self.assertTrue(
            is_donation_interval_eligible(
                last_donation_date,
                'Female'
            )
        )


    def test_female_before_16_weeks_is_not_eligible(self):
        """
        A female donor who has waited less than
        16 weeks should not be eligible.
        """

        last_donation_date = (
            date.today() - timedelta(days=111)
        )

        self.assertFalse(
            is_donation_interval_eligible(
                last_donation_date,
                'Female'
            )
        )


    def test_no_previous_donation_is_eligible(self):
        """
        A donor without a previous donation date
        should pass the donation interval check.
        """

        self.assertTrue(
            is_donation_interval_eligible(
                None,
                'Male'
            )
        )


    def test_system_eligible_donor(self):
        """
        A donor who satisfies all mandatory
        eligibility conditions should pass.
        """

        today = date.today()

        date_of_birth = date(
            today.year - 30,
            today.month,
            today.day
        )

        last_donation_date = (
            today - timedelta(weeks=12)
        )

        result = is_system_eligible(
            date_of_birth,
            'Male',
            last_donation_date,
            True,
            True
        )

        self.assertTrue(result)


    def test_system_ineligible_unavailable_donor(self):
        """
        An otherwise eligible donor who is unavailable
        should fail the system eligibility check.
        """

        today = date.today()

        date_of_birth = date(
            today.year - 30,
            today.month,
            today.day
        )

        last_donation_date = (
            today - timedelta(weeks=12)
        )

        result = is_system_eligible(
            date_of_birth,
            'Male',
            last_donation_date,
            True,
            False
        )

        self.assertFalse(result)


    def test_system_ineligible_medically_ineligible_donor(self):
        """
        A donor who is medically ineligible should
        fail the system eligibility check.
        """

        today = date.today()

        date_of_birth = date(
            today.year - 30,
            today.month,
            today.day
        )

        last_donation_date = (
            today - timedelta(weeks=12)
        )

        result = is_system_eligible(
            date_of_birth,
            'Male',
            last_donation_date,
            False,
            True
        )

        self.assertFalse(result)