from django.contrib import admin  # type: ignore
from django.urls import path, include  # type: ignore
from django.views.generic import TemplateView  # type: ignore
from django.conf import settings  # type: ignore
from django.conf.urls.static import static  # type: ignore
from .views import index_redirect

urlpatterns = [
    # Página raíz
    path("", index_redirect, name="index"),

    # Admin
    path("admin/", admin.site.urls),

    # Apps internas
    path("usuarios/", include("apps.usuarios.urls")),
    path("backoffice/", include("apps.backoffice.urls", namespace="backoffice")),
    path("booking/", include("apps.booking.urls", namespace="booking")),
    path("common/", include("apps.common.urls", namespace="common")),
    path("finanzas/", include("apps.finanzas.urls")),
    path("renta_hoteles/", include("apps.renta_hoteles.urls")),
    path("renta_autos/", include("apps.renta_autos.urls")),
    path("vuelos/", include("apps.vuelos.urls")),
    path("gestion_economica/", include("apps.gestion_economica.urls")),

    # API (mismo archivo de booking, namespace distinto)
    path("api/", include("apps.booking.urls", namespace="booking_api")),

    # Ruta a un template estático si aún lo necesitas
    path("home/", TemplateView.as_view(template_name="index.html"), name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
