from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,\
    AbstractBaseUser
)
from django.utils.crypto import get_random_string
from .validator import(
    validate_check_blacklist,\
    validate_username_regex
)
import string
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .utils import generate_activation_key
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .managers import (
    UserManager,
    EmailActivationManager,
)

import time

User = settings.AUTH_USER_MODEL


class User(AbstractBaseUser):
    def initial_username(
            prefix='nbid_',
            length=35,
            allowed_chars=string.ascii_lowercase + string.digits,
    ):
        suffix = str(time.time())
        _username = prefix + get_random_string(length - len(prefix) - len(suffix), allowed_chars) + suffix
        return _username
    # TODO: clash me babey -_-

    username = models.CharField(
        'username',
        max_length=35,
        unique=True,
        default=initial_username,
        help_text='Required. 50 characters or fewer. Letters, digits and .-_ only.',
        validators=[validate_check_blacklist, validate_username_regex],
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    full_name = models.CharField(max_length=180)
    intro = models.CharField(max_length=140, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    # TODO: add max_length
    phone_number = models.CharField(
        'phone number',
        max_length=15,
        unique=True,
        blank=True,
        null=True
    )
    # TODO: phone number verification
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )
    avatar = models.ImageField(blank=True)
    # TODO: add default as random avatar
    birth_date = models.DateField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'username']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.full_name

    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        # Simplest possible answer: Yes, always
        return True

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def is_staff(self):
        """Is the user a member of staff?"""
        # Simplest possible answer: All admins are staff
        return self.is_admin


class EmailActivation(models.Model):
    ACCOUNT_ACTIVATION_DAYS = 2

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=255)
    key = models.CharField(max_length=256)
    attempt = models.IntegerField(default=0)
    expires = models.IntegerField(default=ACCOUNT_ACTIVATION_DAYS)
    last_sent_mail = models.DateTimeField(blank=True, null=True)
    forced_expired = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    objects = EmailActivationManager()

    def is_time_expired(self):
        if self.last_sent_mail:
            return self.last_sent_mail + timedelta(2) < timezone.now()
        else:
            return False

    def is_forced_expired(self):
        return self.forced_expired

    def is_expired(self):
        return self.is_time_expired() or self.forced_expired


def post_save_user_create_reciever(sender, instance, created, *args, **kwargs):
    if created:
        print(instance.id)
        EmailActivation.objects.create_key(instance=instance)


post_save.connect(post_save_user_create_reciever, sender=User)
