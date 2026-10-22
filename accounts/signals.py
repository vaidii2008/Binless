"""Set up a new member's organisation and shop as soon as they sign up."""

from allauth.account.signals import user_signed_up
from django.db import transaction
from django.dispatch import receiver

from orders.plans import open_simulated_shop

from .models import Membership, Organisation


@receiver(user_signed_up)
def set_up_new_member(sender, request, user, **kwargs) -> None:
    """Give a new member their own organisation, as its owner, and a simulated shop."""
    with transaction.atomic():
        organisation = Organisation.objects.create(name=user.email)
        Membership.objects.create(
            user=user, organisation=organisation, role=Membership.Role.OWNER
        )
        open_simulated_shop(organisation)
