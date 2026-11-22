from datetime import date, timedelta


def calculate_age(date_of_birth):
    today = date.today()

    age = today.year - date_of_birth.year

    if (today.month, today.day) < (
        date_of_birth.month,
        date_of_birth.day
    ):
        age -= 1

    return age


def is_age_eligible(date_of_birth):
    age = calculate_age(date_of_birth)

    return 18 <= age <= 65


def get_minimum_donation_interval(gender):
    """
    Returns the minimum recommended interval between
    whole-blood donations based on donor gender.

    WHO baseline:
    - Male: 12 weeks
    - Female: 16 weeks
    """

    gender = gender.strip().lower()

    if gender == 'male':
        return timedelta(weeks=12)

    if gender == 'female':
        return timedelta(weeks=16)

    return None


def is_donation_interval_eligible(
    last_donation_date,
    gender,
):
    """
    Determines whether the donor has waited the
    minimum recommended interval since their
    previous whole-blood donation.
    """

    if not last_donation_date:
        return True

    minimum_interval = get_minimum_donation_interval(gender)

    if minimum_interval is None:
        return False

    next_eligible_date = (
        last_donation_date + minimum_interval
    )

    return date.today() >= next_eligible_date


def is_system_eligible(
    date_of_birth,
    gender,
    last_donation_date,
    is_medically_eligible,
    is_available,
):
    """
    Determines whether a donor passes all mandatory
    eligibility requirements.
    """

    age_eligible = is_age_eligible(date_of_birth)

    donation_eligible = is_donation_interval_eligible(
        last_donation_date,
        gender,
    )

    return (
        age_eligible
        and donation_eligible
        and is_medically_eligible
        and is_available
    )