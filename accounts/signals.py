def post_save_user_handler(sender, instance, created, *args, **kwargs):
    """
    post_save handler of User model.
    """
    print("inside post_save")
    if created and instance:
        # user has been created
        # create corresponding `types` related models (i.e. TeacherMore, StudentMore) if needed
        if len(instance.types) > 0:
            print(f'len = {len(instance.types)}')
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
