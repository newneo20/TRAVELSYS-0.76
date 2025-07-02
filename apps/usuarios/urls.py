from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from .views import login_view

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', login_view, name='login'),  # Vista personalizada de login
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Gestión de usuarios
    path('', views.listar_usuarios, name='listar_usuarios'),  # ← ahora accesible desde /usuarios/
    path('crear/', views.crear_usuario, name='crear_usuario'),
    path('editar/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
    path('eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),

    # Utilidad
    path('check-session/', views.check_session_status, name='check_session'),
]
