# usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import UserRegisterForm, UserUpdateForm, PerfilUpdateForm, RolForm, AsignarRolForm
from .models import Rol, Perfil
from django.contrib.auth.decorators import user_passes_test

def es_admin(user):
    if not user.is_authenticated:
        return False
    # Los superusuarios siempre son considerados administradores
    if user.is_superuser:
        return True
    try:
        perfil = Perfil.objects.get(usuario=user)
        return perfil.rol and perfil.rol.nombre == 'Administrador'
    except (Perfil.DoesNotExist, AttributeError):
        return False

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                # Crear el usuario
                user = form.save()
                
                # Verificar si ya tiene perfil (por las señales)
                try:
                    perfil = user.perfil
                except Perfil.DoesNotExist:
                    # Si no tiene perfil, crearlo manualmente
                    rol_cliente, _ = Rol.objects.get_or_create(
                        nombre='Cliente',
                        defaults={'descripcion': 'Usuario que solicita servicios'}
                    )
                    
                    Perfil.objects.create(
                        usuario=user,
                        rol=rol_cliente
                    )
                
                username = form.cleaned_data.get('username')
                messages.success(request, f'Cuenta creada para {username}! Ahora puedes iniciar sesión.')
                return redirect('login')
                
            except Exception as e:
                # Si hay error, eliminar el usuario creado para evitar inconsistencias
                if 'user' in locals():
                    user.delete()
                messages.error(request, f'Error al crear la cuenta: {str(e)}')
    else:
        form = UserRegisterForm()
    return render(request, 'usuarios/register.html', {'form': form})

@login_required
def profile(request):
    # Asegurar que el usuario tenga un perfil
    try:
        perfil = request.user.perfil
    except Perfil.DoesNotExist:
        # Crear perfil si no existe
        rol_cliente, _ = Rol.objects.get_or_create(
            nombre='Cliente',
            defaults={'descripcion': 'Usuario que solicita servicios'}
        )
        perfil = Perfil.objects.create(
            usuario=request.user,
            rol=rol_cliente
        )
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = PerfilUpdateForm(request.POST, instance=perfil)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Tu perfil ha sido actualizado!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = PerfilUpdateForm(instance=perfil)
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
    }
    return render(request, 'usuarios/profile.html', context)

@login_required
@user_passes_test(es_admin)
def crear_rol(request):
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rol creado exitosamente!')
            return redirect('lista_roles')
    else:
        form = RolForm()
    return render(request, 'usuarios/rol_form.html', {'form': form})

@login_required
@user_passes_test(es_admin)
def lista_roles(request):
    roles = Rol.objects.all()
    return render(request, 'usuarios/lista_roles.html', {'roles': roles})

@login_required
@user_passes_test(es_admin)
def lista_usuarios(request):
    usuarios = User.objects.all()
    return render(request, 'usuarios/lista_usuarios.html', {'usuarios': usuarios})

@login_required
@user_passes_test(es_admin)
def asignar_rol(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    perfil, created = Perfil.objects.get_or_create(usuario=usuario)
    
    if request.method == 'POST':
        form = AsignarRolForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, f'Rol asignado a {usuario.username} correctamente!')
            return redirect('lista_usuarios')
    else:
        form = AsignarRolForm(instance=perfil)
    
    return render(request, 'usuarios/asignar_rol.html', {'form': form, 'usuario': usuario})

@login_required
def dashboard(request):
    # Verificar y crear el perfil si no existe
    try:
        perfil = request.user.perfil
    except Perfil.DoesNotExist:
        rol_cliente, _ = Rol.objects.get_or_create(
            nombre='Cliente',
            defaults={'descripcion': 'Usuario que solicita servicios'}
        )
        perfil = Perfil.objects.create(
            usuario=request.user,
            rol=rol_cliente
        )
    
    context = {
        'title': 'Dashboard',
    }
    return render(request, 'usuarios/dashboard.html', context)

@login_required
def lista_roles(request):
    # Verificar si el usuario es administrador
    if not es_admin(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('dashboard')
    
    roles = Rol.objects.all()
    return render(request, 'usuarios/lista_roles.html', {'roles': roles})

@login_required
def crear_rol(request):
    # Verificar si el usuario es administrador
    if not es_admin(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rol creado exitosamente!')
            return redirect('lista_roles')
    else:
        form = RolForm()
    return render(request, 'usuarios/rol_form.html', {'form': form})

@login_required
def lista_usuarios(request):
    # Verificar si el usuario es administrador
    if not es_admin(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('dashboard')
    
    usuarios = User.objects.all()
    return render(request, 'usuarios/lista_usuarios.html', {'usuarios': usuarios})

@login_required
def asignar_rol(request, user_id):
    # Verificar si el usuario es administrador
    if not es_admin(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('dashboard')
    
    usuario = get_object_or_404(User, id=user_id)
    perfil, created = Perfil.objects.get_or_create(usuario=usuario)
    
    if request.method == 'POST':
        form = AsignarRolForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, f'Rol asignado a {usuario.username} correctamente!')
            return redirect('lista_usuarios')
    else:
        form = AsignarRolForm(instance=perfil)
    
    return render(request, 'usuarios/asignar_rol.html', {'form': form, 'usuario': usuario})