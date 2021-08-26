# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#


from django.db import transaction as tx
from django.db import IntegrityError
from django.utils.translation import ugettext as _

from django.apps import apps

from taiga.base.utils.slug import slugify_uniquely
from taiga.base import exceptions as exc
from taiga.auth.services import send_register_email
from taiga.auth.services import make_auth_response_data, get_membership_by_token
from taiga.auth.signals import user_registered as user_registered_signal

from . import connector


@tx.atomic
def threefold_register(username:str, email:str, full_name:str, threefold_id:int, bio:str, token:str=None):
    """
    Register a new user from threefold.

    This can raise `exc.IntegrityError` exceptions in
    case of conflics found.

    :returns: User
    """
    auth_data_model = apps.get_model("users", "AuthData")
    user_model = apps.get_model("users", "User")

    try:
        # threefold user association exist?
        auth_data = auth_data_model.objects.get(key="threefold", value=threefold_id)
        user = auth_data.user
    except auth_data_model.DoesNotExist:
        try:
            # Is a user with the same email as the threefold user?
            user = user_model.objects.get(email=email)
            auth_data_model.objects.create(user=user, key="threefold", value=threefold_id, extra={})
        except user_model.DoesNotExist:
            # Create a new user
            username_unique = slugify_uniquely(username, user_model, slugfield="username")
            user = user_model.objects.create(email=email,
                                             username=username_unique,
                                             full_name=full_name,
                                             bio=bio)
            auth_data_model.objects.create(user=user, key="threefold", value=threefold_id, extra={})

            send_register_email(user)
            user_registered_signal.send(sender=user.__class__, user=user)

    if token:
        membership = get_membership_by_token(token)

        try:
            membership.user = user
            membership.save(update_fields=["user"])
        except IntegrityError:
            raise exc.IntegrityError(_("This user is already a member of the project."))

    return user


def threefold_login_func(request):
    signedAttempt = request.DATA.get('signedAttempt', None)
    redirectUri = request.DATA.get('redirectUri', None)
    state = request.DATA.get('state', None)
    email, user_info = connector.me(signedAttempt, state, redirectUri)

    user = threefold_register(username=user_info.username,
                           email=email,
                           full_name=user_info.full_name,
                           threefold_id=user_info.id,
                           bio=user_info.bio)
    data = make_auth_response_data(user)
    return data
