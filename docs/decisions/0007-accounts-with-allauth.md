# 7. Accounts with django-allauth, and a simulated shop for every new member

Date: October 2026

## Context

Shop owners need their own sign-in before Binless can hold their sales. Until CSV upload exists, a new member has no data of their own, but a recruiter or a shop owner trying Binless should still see the order page as a member would.

## Decision

Members sign up and sign in with an email address and a password, using django-allauth. Email addresses aren't verified yet, because Binless doesn't send email. Signing up creates an organisation with the member as its owner, and a simulated shop that starts from the sample shop's latest order. The nightly batch writes the same plans to every simulated shop. Members reach shops only through `Store.objects.for_user`, and any other shop returns a 404. Deleting an account deletes any organisation it leaves without members, with its shops.

## Consequences

- allauth handles sign-up, sign-in, sessions, rate limits and password checks, and already has email verification and password reset for when Binless sends email.
- A member who forgets their password can't reset it yet.
- Each member adds 20 forecasts a night to the batch. A few hundred members would call for bulk writes.
- Binless now stores personal data, an email address and a password hash, so account deletion was built at the same time.
- The batch is the one piece of code that reads shops across organisations.
