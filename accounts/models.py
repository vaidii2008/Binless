"""Organisations, the people in them, and the rule that every row belongs to one."""

from django.conf import settings
from django.db import models

SAMPLE_ORGANISATION_NAME = "Sample organisation (simulated)"


class Organisation(models.Model):
    """A business that owns one or more shops."""

    name = models.CharField(max_length=100, unique=True)
    # The simulated organisation whose shop anyone can see without signing in.
    is_sample = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Membership(models.Model):
    """One user's role in one organisation."""

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MANAGER = "manager", "Manager"
        STAFF = "staff", "Staff"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STAFF)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=["user", "organisation"], name="one_membership_per_organisation"
            ),
        )

    def __str__(self) -> str:
        return f"{self.user} ({self.get_role_display()}) in {self.organisation}"


class OrganisationQuerySet(models.QuerySet):
    """Queries that return one organisation's rows, or the rows a user may see."""

    def for_organisation(self, organisation: Organisation) -> "OrganisationQuerySet":
        """Return the rows that belong to organisation."""
        return self.filter(organisation=organisation)

    def for_user(self, user) -> "OrganisationQuerySet":
        """Return the rows in every organisation the user is a member of."""
        return self.filter(organisation__memberships__user=user)


class OrganisationOwned(models.Model):
    """Base for every table whose rows belong to one organisation."""

    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="%(class)ss"
    )

    objects = OrganisationQuerySet.as_manager()

    class Meta:
        abstract = True
