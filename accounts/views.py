from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(["GET", "POST"])
def delete_account(request: HttpRequest) -> HttpResponse:
    """Ask to confirm, then delete the member and any organisation left with no one."""
    if request.method == "GET":
        return render(request, "accounts/delete_account.html")
    user = request.user
    organisations = [membership.organisation for membership in user.memberships.all()]
    logout(request)
    with transaction.atomic():
        user.delete()
        for organisation in organisations:
            if not organisation.memberships.exists():
                organisation.delete()
    messages.success(request, "Your account, organisation and shops have been deleted.")
    return redirect("home")
