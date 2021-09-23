from django.contrib import auth
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.contrib.postgres.fields import ArrayField
from django.core.mail import send_mail
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
from model_utils.models import TimeStampedModel

from .validators import UnicodeUsernameValidator


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)

    def with_perm(self, perm, is_active=True, include_superusers=True, backend=None, obj=None):
        if backend is None:
            backends = auth._get_backends(return_tuples=True)
            if len(backends) == 1:
                backend, _ = backends[0]
            else:
                raise ValueError(
                    'You have multiple authentication backends configured and '
                    'therefore must provide the `backend` argument.'
                )
        elif not isinstance(backend, str):
            raise TypeError(
                'backend must be a dotted import path string (got %r).'
                % backend
            )
        else:
            backend = auth.load_backend(backend)
        if hasattr(backend, 'with_perm'):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()


class TeacherManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(types__contains=[User.TypesChoices.TEACHER])


class StudentManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(types__contains=[User.TypesChoices.STUDENT])


class GuardianManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(types__contains=[User.TypesChoices.GUARDIAN])


class CommitteeManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(types__contains=[User.TypesChoices.COMMITTEE])


class AbstractUser(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Username and password are required. Other fields are optional.
    """
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = True

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


class User(AbstractUser):
    """
    Users within the Django authentication system are represented by this
    model.

    Username and password are required. Other fields are optional.
    """
    class TypesChoices(models.TextChoices):
        TEACHER = 'TEACHER', _('Teacher')
        STUDENT = 'STUDENT', _('Student')
        GUARDIAN = 'GUARDIAN', _('Guardian')
        COMMITTEE = 'COMMITTEE', _('Committee')

    types = ArrayField(
        models.CharField(max_length=10, choices=TypesChoices.choices),
        size=4,
        null=True,
        blank=True,
    )
    modified = models.DateTimeField(auto_now=True, auto_now_add=False)

    # to track changes in model fields
    types_tracker = FieldTracker(fields=['types'])



class TeacherMore(TimeStampedModel):
    designation = models.CharField(max_length=20, null=True, blank=True)
    user = models.OneToOneField(User, related_name='teachermore', on_delete=models.CASCADE)


class Teacher(User):
    types = [User.TypesChoices.TEACHER]
    objects = TeacherManager()

    @property
    def more(self):
        return self.teachermore
    
    class Meta:
        proxy = True


class StudentMore(TimeStampedModel):
    level = models.CharField(max_length=20, null=True, blank=True)
    user = models.OneToOneField(User, related_name='studentmore', on_delete=models.CASCADE)


class Student(User):
    types = [User.TypesChoices.STUDENT]
    objects = StudentManager()

    @property
    def more(self):
        self.studentmore
    
    class Meta:
        proxy = True


class GuardianMore(TimeStampedModel):
    occupation = models.CharField(max_length=50, null=True, blank=True)
    user = models.OneToOneField(User, related_name='guardianmore', on_delete=models.CASCADE)


class Guardian(User):
    types = [User.TypesChoices.GUARDIAN]
    objects = GuardianManager()

    @property
    def more(self):
        return self.guardianmore
    
    class Meta:
        proxy = True


class CommitteeMore(TimeStampedModel):
    designation = models.CharField(max_length=20, null=True, blank=True)
    user = models.OneToOneField(User, related_name='committeemore', on_delete=models.CASCADE)


class Committee(User):
    types = [User.TypesChoices.COMMITTEE]
    objects = CommitteeManager()
    
    @property
    def more(self):
        return self.committeemore
    
    class Meta:
        proxy = True


@receiver(post_save, sender=User)
def post_save_user_handler(sender, instance, created, *args, **kwargs):
    """
    post_save handler of User model.
    """
    # print("inside post_save")
    if created and instance:
        # user has been created
        # create corresponding `types` related models (i.e. TeacherMore, StudentMore) if needed
        if instance.types and len(instance.types) > 0:
            # print(f'len = {len(instance.types)}')
            if instance.TypesChoices.TEACHER in instance.types:
                # create TeacherMore
                from accounts.models import TeacherMore
                _ = TeacherMore.objects.create(user=instance)
            if instance.TypesChoices.STUDENT in instance.types:
                # create StudentMore
                from accounts.models import StudentMore
                _ = StudentMore.objects.create(user=instance)
            if instance.TypesChoices.GUARDIAN in instance.types:
                # create GuardianMore
                from accounts.models import GuardianMore
                _ = GuardianMore.objects.create(user=instance)
            if instance.TypesChoices.COMMITTEE in instance.types:
                # create CommitteeMore
                from accounts.models import CommitteeMore
                _ = CommitteeMore.objects.create(user=instance)
