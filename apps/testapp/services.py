import requests
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def get_google_access_token(code):
    if not all((settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET, settings.GOOGLE_REDIRECT_URI)):
        raise AuthenticationFailed("Google OAuth не настроен на сервере.")

    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    try:
        response = requests.post(GOOGLE_TOKEN_URL, data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise AuthenticationFailed("Не удалось обменять Google code на токен.") from exc

    if not isinstance(data, dict):
        raise AuthenticationFailed("Google вернул некорректный ответ при обмене code.")

    access_token = data.get("access_token")
    if not access_token:
        raise AuthenticationFailed("Google не вернул access_token.")
    return access_token


def get_google_user_info(access_token):
    try:
        response = requests.get(
            GOOGLE_USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise AuthenticationFailed("Не удалось получить профиль Google.") from exc

    if not isinstance(data, dict):
        raise AuthenticationFailed("Google вернул некорректные данные профиля.")

    email = data.get("email")
    if not email or not data.get("email_verified", False):
        raise AuthenticationFailed("Google не подтвердил адрес электронной почты.")

    return {
        "email": email,
        "name": data.get("name") or "",
    }
