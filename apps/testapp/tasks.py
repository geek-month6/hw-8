from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone


@shared_task
def send_welcome_email_task(user_email):
    send_mail(
        subject="Добро пожаловать!",
        message="Спасибо за регистрацию!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )
    return f"Приветственное письмо отправлено: {user_email}"


@shared_task
def clean_inactive_users_task(days=30):
    User = get_user_model()
    cutoff_date = timezone.now() - timedelta(days=days)
    inactive_users = User.objects.filter(
        is_active=False,
        date_joined__lt=cutoff_date,
    )
    count = inactive_users.count()
    inactive_users.delete()
    return f"Удалено неактивных пользователей: {count}"


@shared_task
def send_daily_admin_report_task():
    User = get_user_model()
    roles = ("ADMIN", "MODERATOR", "USER")
    statistics = {
        role: User.objects.filter(role=role).count()
        for role in roles
    }
    print("Статистика пользователей по ролям:", statistics)
    return statistics
