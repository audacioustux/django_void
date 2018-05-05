from django.contrib.auth.models import BaseUserManager
from django.db import models
from django.db import transaction
from .utils import generate_activation_key
from django.db.models import Q
import hashlib
from django.utils.timezone import now
from smtplib import SMTPException
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist

# TODO: clean this massy imports

class EmailActivationManager(models.Manager):
    def create_key(self, instance):  # user instance passed in
        key = generate_activation_key()
        key_instance = self.model(
            user=instance,
            email=instance.email,
            key=key,
        )
        try:
            instance.email_user(
                subject="activation code",
                message=key+'&'+instance.email
            )
        except SMTPException:
            pass
        # TODO: send error to api payload
        else:
            key_instance.last_sent_mail = now()

        key_instance.save()
        return key_instance

    def refresh_key(self):
        pass

    def verify_key(self, key, email):
        try:
            key_entry = self.get(email=email, key=key)
        except ObjectDoesNotExist:
            print("wrong key")
            # TODO: send error to api payload
        else:
            if not key_entry.is_expired():
                key_entry.verified = True
                key_entry.save()
                key_entry.user.objects.make_active()
                return email


class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password, username=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        if not full_name:
            raise ValueError('users must have an full name')

        user = self.model(
            email=self.normalize_email(email),
            full_name=full_name,
        )
        if username:
            user.username = self.model.normalize_username(username)

        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, email, full_name, password, username):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            full_name,
            password,
            username,
        )
        user.is_active = True
        user.is_admin = True
        user.save()
        return user

    def make_active(self, active):
        user = self.model(
            is_active=active
        )
        user.save()
        return user.is_active
