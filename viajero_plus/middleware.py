# viajero_plus/middleware.py

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from datetime import datetime

class AutoLogoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return

        last_activity_str = request.session.get('last_activity')
        now = timezone.now()

        if last_activity_str:
            try:
                # Convertimos string a datetime aware
                last_activity = timezone.make_aware(
                    datetime.strptime(last_activity_str, "%Y-%m-%d %H:%M:%S"),
                    timezone.get_current_timezone()
                )
                elapsed_time = (now - last_activity).total_seconds()

                if elapsed_time > settings.SESSION_COOKIE_AGE:
                    logout(request)
                    return redirect(settings.LOGIN_URL)

            except Exception:
                # Si ocurre error en el parseo de la fecha, forzamos cierre de sesión
                logout(request)
                return redirect(settings.LOGIN_URL)

        # Guardamos timestamp actual en la sesión
        request.session['last_activity'] = now.strftime("%Y-%m-%d %H:%M:%S")
