from datetime import date

from .eligibility import (
    is_system_eligible,
    get_minimum_donation_interval,
)


BLOOD_COMPATIBILITY = {
    'O-': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'],
    'O+': ['O+', 'A+', 'B+', 'AB+'],
    'A-': ['A-', 'A+', 'AB-', 'AB+'],
    'A+': ['A+', 'AB+'],
    'B-': ['B-', 'B+', 'AB-', 'AB+'],
    'B+': ['B+', 'AB+'],
    'AB-': ['AB-', 'AB+'],
    'AB+': ['AB+'],
}


def is_blood_compatible(
    donor_blood_group,
    recipient_blood_group,
):
    compatible_groups = BLOOD_COMPATIBILITY.get(
        donor_blood_group,
        []
    )

    return recipient_blood_group in compatible_groups


def calculate_location_score(
    donor_state,
    donor_city,
    request_state,
    request_city,
):
    donor_state = donor_state.strip().lower()
    donor_city = donor_city.strip().lower()

    request_state = request_state.strip().lower()
    request_city = request_city.strip().lower()

    if (
        donor_state == request_state
        and donor_city == request_city
    ):
        return 2

    if donor_state == request_state:
        return 1

    return 0


def filter_mandatory_criteria(
    donor,
    recipient_blood_group,
):
    """
    Stage 1: Applies the mandatory donor filters.

    A donor must:
    - be age eligible
    - satisfy the donation interval
    - be medically eligible
    - be available
    - have compatible blood
    """

    if not is_system_eligible(
        donor.date_of_birth,
        donor.gender,
        donor.last_donation_date,
        donor.is_medically_eligible,
        donor.is_available,
    ):
        return False

    if not is_blood_compatible(
        donor.blood_group,
        recipient_blood_group,
    ):
        return False

    return True


def filter_by_proximity(
    donor,
    request_state,
    request_city,
):
    """
    Stage 2: Applies the proximity/location filter.

    Donors outside the requested state are excluded.
    """

    location_score = calculate_location_score(
        donor.state,
        donor.city,
        request_state,
        request_city,
    )

    return location_score > 0


def calculate_proximity_score(
    location_score,
):
    """
    Converts the location score to a 0–100
    proximity score.

    Same city and state = 100
    Same state, different city = 60
    Different state = 0
    """

    if location_score == 2:
        return 100

    if location_score == 1:
        return 60

    return 0


def calculate_readiness_score(
    gender,
    last_donation_date,
):
    """
    Calculates readiness based on the number of
    days beyond the minimum donation interval.

    0 days beyond minimum = 0
    30 days = 16.7
    60 days = 33.3
    90 days = 50
    120 days = 66.7
    150 days = 83.3
    180+ days = 100
    """

    if not last_donation_date:
        return 100

    minimum_interval = get_minimum_donation_interval(
        gender
    )

    if minimum_interval is None:
        return 0

    next_eligible_date = (
        last_donation_date + minimum_interval
    )

    days_beyond_minimum = (
        date.today() - next_eligible_date
    ).days

    if days_beyond_minimum <= 0:
        return 0

    readiness_score = (
        days_beyond_minimum / 180
    ) * 100

    return min(readiness_score, 100)


def calculate_weighted_score(
    proximity_score,
    readiness_score,
):
    """
    Calculates the final matching score.

    Proximity = 60%
    Readiness = 40%
    """

    return (
        (0.60 * proximity_score)
        + (0.40 * readiness_score)
    )


def calculate_match_score(
    donor,
    recipient_blood_group,
    request_state,
    request_city,
):
    """
    Runs the complete matching process for one donor.

    Returns the matching score components:
    - proximity score
    - readiness score
    - final weighted score

    Returns None if the donor fails a mandatory
    matching criterion.
    """

    # Stage 1: Mandatory filtering
    if not filter_mandatory_criteria(
        donor,
        recipient_blood_group,
    ):
        return None

    # Stage 2: Proximity filtering
    if not filter_by_proximity(
        donor,
        request_state,
        request_city,
    ):
        return None

    location_score = calculate_location_score(
        donor.state,
        donor.city,
        request_state,
        request_city,
    )

    # Stage 3: Calculate proximity score
    proximity_score = calculate_proximity_score(
        location_score
    )

    # Stage 3: Calculate readiness score
    readiness_score = calculate_readiness_score(
        donor.gender,
        donor.last_donation_date,
    )

    # Stage 4: Calculate final weighted score
    final_score = calculate_weighted_score(
        proximity_score,
        readiness_score,
    )

    return {
        'proximity_score': proximity_score,
        'readiness_score': readiness_score,
        'final_score': final_score,
    }

def rank_donors(
    donors,
    recipient_blood_group,
    request_state,
    request_city,
):
    """
    Calculates and ranks eligible donors from highest
    matching score to lowest matching score.
    """

    ranked_donors = []

    for donor in donors:

        match_result = calculate_match_score(
            donor,
            recipient_blood_group,
            request_state,
            request_city,
        )

        if match_result is not None:

            ranked_donors.append(
                {
                    'donor': donor,
                    'proximity_score': match_result[
                        'proximity_score'
                    ],
                    'readiness_score': match_result[
                        'readiness_score'
                    ],
                    'score': match_result[
                        'final_score'
                    ],
                }
            )

    ranked_donors.sort(
    key=lambda match: (
        match['score'],
        match['proximity_score'],
        match['readiness_score'],
        -match['donor'].id,
    ),
    reverse=True,
)
    return ranked_donors