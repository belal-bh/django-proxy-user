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
    """
    Customized Manager for custom User model with additional fields and features.
    """
    use_in_migrations = True
    
    @classmethod
    def normalize_types(cls, types: list):
        """
        Normalize the types list by sorting and removing duplicate items.
        """
        if not isinstance(types, (list, set)):
            types = list()
        elif isinstance(types, set):
            types = list(types)
        from accounts.models import User
        valid_types_set = set([t for t, _ in User.TypesChoices.choices])
        types_set_validated = valid_types_set.intersection(set(types))
        types = list(types_set_validated)
        types.sort()
        return types

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
        default=list, # default value as an empty list
        blank=True,
    )
    modified = models.DateTimeField(auto_now=True, auto_now_add=False)

    # to track changes in model fields
    types_tracker = FieldTracker(fields=['types'])
    
    def clean(self):
        super().clean()
        self.types = self.__class__.objects.normalize_types(self.types)
    
    def save(self, *args, **kwargs):
        # normalize types before calling super().save()
        # otherwise post_save signal will be called before normalize types
        self.types = self.__class__.objects.normalize_types(self.types)
        super().save(*args, **kwargs)


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
            # print(f"instance.types (created)={instance.types}")
            from accounts.models import (CommitteeMore, GuardianMore,
                                         StudentMore, TeacherMore)
            if instance.TypesChoices.TEACHER in instance.types:
                # create TeacherMore
                _ = TeacherMore.objects.create(user=instance)
            if instance.TypesChoices.STUDENT in instance.types:
                # create StudentMore
                _ = StudentMore.objects.create(user=instance)
            if instance.TypesChoices.GUARDIAN in instance.types:
                # create GuardianMore
                _ = GuardianMore.objects.create(user=instance)
            if instance.TypesChoices.COMMITTEE in instance.types:
                # create CommitteeMore
                _ = CommitteeMore.objects.create(user=instance)
        
    elif instance and instance.types_tracker.has_changed('types'):
        # print(f"instance.types (chnaged)={instance.types}")
        from accounts.models import (CommitteeMore, GuardianMore,
                                         StudentMore, TeacherMore)
        # user types has been changed
        # create corresponding `types` related models (i.e. TeacherMore, StudentMore) if needed
        previous_types_set = set(instance.types_tracker.previous('types') if instance.types_tracker.previous('types') else list())
        current_types_set = set(instance.types if instance.types else list())
        removed_types_set = previous_types_set - current_types_set
        added_types_set = current_types_set - previous_types_set
        # print(f"previous_types_set={previous_types_set}, current_types_set={current_types_set}, \
        #     removed_types_set={removed_types_set}, added_types_set={added_types_set}")
        
        # create or update (if needed. i.e. change active=True if already exist) 
        # corresponding `types` (added_types_set) related models
        if len(added_types_set) > 0:
            # print(f"adding added_types_set:{added_types_set}")
            for user_type in added_types_set:
                if user_type == instance.TypesChoices.TEACHER:
                    # create or update TeacherMore
                    _ = TeacherMore.objects.update_or_create(user=instance)
                elif user_type == instance.TypesChoices.STUDENT:
                    # create or update StudentMore
                    _ = StudentMore.objects.update_or_create(user=instance)
                elif user_type == instance.TypesChoices.GUARDIAN:
                    # create or update GuardianMore
                    _ = GuardianMore.objects.update_or_create(user=instance)
                elif user_type == instance.TypesChoices.COMMITTEE:
                    # create or update CommitteeMore
                    _ = CommitteeMore.objects.update_or_create(user=instance)
        
        # update (if exist) corresponding `types` (removed_types_set) related models
        if len(removed_types_set) > 0:
            # print(f"removing removed_types_set:{removed_types_set}")
            for user_type in removed_types_set:
                if user_type == instance.TypesChoices.TEACHER:
                    try:
                        # check obj of user_type exist
                        obj = TeacherMore.objects.get(user=instance)
                        # do something of this obj if needed, i.e. update active=False
                    except TeacherMore.DoesNotExist:
                        pass
                elif user_type == instance.TypesChoices.STUDENT:
                    try:
                        # check obj of user_type exist
                        obj = StudentMore.objects.get(user=instance)
                        # do something of this obj if needed, i.e. update active=False
                    except StudentMore.DoesNotExist:
                        pass
                elif user_type == instance.TypesChoices.GUARDIAN:
                    try:
                        # check obj of user_type exist
                        obj = GuardianMore.objects.get(user=instance)
                        # do something of this obj if needed, i.e. update active=False
                    except GuardianMore.DoesNotExist:
                        pass
                elif user_type == instance.TypesChoices.COMMITTEE:
                    try:
                        # check obj of user_type exist
                        obj = CommitteeMore.objects.get(user=instance)
                        # do something of this obj if needed, i.e. update active=False
                    except CommitteeMore.DoesNotExist:
                        pass
