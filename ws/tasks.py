from datetime import timedelta
import logging
import random

from celery import group, shared_task
from django.core.cache import cache
from django.db.models import Q

from ws import models
from ws import settings
from ws.sao import send_email_to_funds
from ws.utils import dates as date_utils
from ws.utils import geardb, member_sheets
from ws.lottery.run import SingleTripLotteryRunner, WinterSchoolLotteryRunner


logger = logging.getLogger(__name__)


def acquire_lock(discount, lock_expires_after=300):
    """ Generate a lock on the discount's Google sheet.

    Because cache adds are an atomic operation, we can use this
    to create a lock (that will automatically expire if not unset).
    Returns True if the key was added, False if already present.
    """
    return cache.add(discount.ga_key, 'true', lock_expires_after)


def release_lock(discount):
    """ Mark the sheet as updated and free to be locked by another task. """
    return cache.delete(discount.ga_key)


def increasing_retry(num_retries):
    """ Returning an increasing countdown (in seconds).

    Includes randomness to avoid the Thundering Herd Problem.
    """
    return int(random.uniform(2, 4) ** num_retries)


@shared_task(bind=True, max_retries=4)
def update_discount_sheet(self, discount_id):
    """ Overwrite the sheet to include all members desiring the discount.

    This is the only means of removing users if they no longer
    wish to share their information, so it should be run periodically.
    """
    discount = models.Discount.objects.get(pk=discount_id)
    logger.info("Updating the discount sheet for %s", discount.name)

    if settings.DISABLE_GSHEETS:
        logger.warning("Google Sheets functionality is disabled, "
                       "not updating sheet for '%s'", discount.name)
        return

    if acquire_lock(discount):
        try:
            member_sheets.update_discount_sheet(discount)
        finally:
            release_lock(discount)
    else:
        self.retry(countdown=increasing_retry(self.request.retries))


@shared_task
def update_all_discount_sheets():
    logger.info("Updating the member roster for all discount sheets")
    discount_pks = models.Discount.objects.values_list('pk', flat=True)
    group([update_discount_sheet.s(pk) for pk in discount_pks])()


@shared_task
def update_participant_affiliation(participant_id):
    """ Use the participant's affiliation to update the gear database. """
    participant = models.Participant.objects.get(pk=participant_id)
    geardb.update_affiliation(participant)


@shared_task
def send_sao_itineraries():
    """ Email trip itineraries to the Student Activities Office.

    This task should be run daily, so that it will always send SAO
    this information _before_ the trip actually starts.
    """
    tomorrow = date_utils.local_date() + timedelta(days=1)
    trips = models.Trip.objects.filter(trip_date=tomorrow, info__isnull=False)
    logger.info("Sending itineraries for %d trips taking place tomorrow, %s",
                trips.count(), tomorrow)
    for trip in trips.select_related('info').prefetch_related('leaders'):
        send_email_to_funds(trip)


@shared_task
def run_ws_lottery():
    logger.info("Commencing Winter School lottery run")
    runner = WinterSchoolLotteryRunner()
    runner()


@shared_task
def purge_non_student_discounts():
    """ Purge non-students from student-only discounts.

    Student eligibility is enforced at the API and form level. If somebody was
    a student at the time of enrolling but is no longer a student, we should
    unenroll them.
    """
    logger.info("Purging non-students from student-only discounts")
    stu_discounts = models.Discount.objects.filter(student_required=True)
    not_student = ~Q(affiliation__in=models.Participant.STUDENT_AFFILIATIONS)

    # Remove student discounts from all non-students who have them
    participants = models.Participant.objects.all()
    for par in participants.filter(not_student, discounts__in=stu_discounts):
        par.discounts = par.discounts.filter(student_required=True)
        par.save()


@shared_task(bind=True, max_retries=4)
def update_participant(self, discount_id, participant_id):
    """ Lock the sheet and add/update a single participant. """
    discount = models.Discount.objects.get(pk=discount_id)
    participant = models.Participant.objects.get(pk=participant_id)

    if settings.DISABLE_GSHEETS:
        logger.warning("Google Sheets functionality is disabled, not updating "
                       "'%s' for %s", discount.name, participant.name)
        return

    if acquire_lock(discount):
        try:
            member_sheets.update_participant(discount, participant)
        finally:
            release_lock(discount)
    else:
        self.retry(countdown=increasing_retry(self.request.retries))


@shared_task
def run_lottery(trip_id, lottery_config=None):
    """ Run a lottery algorithm for the given trip (idempotent).

    If running on a trip that isn't in lottery mode, this won't make
    any changes (making this task idempotent).
    """
    logger.info("Running lottery for trip #%d", trip_id)
    trip = models.Trip.objects.get(pk=trip_id)
    runner = SingleTripLotteryRunner(trip)
    runner()
