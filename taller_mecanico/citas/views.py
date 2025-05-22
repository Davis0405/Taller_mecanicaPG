# citas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Vehiculo, Cita, TipoServicio, Notificacion
from .forms import VehiculoForm, CitaForm, FechaHoraDisponibleForm, GestionCitaForm
from django.utils import timezone
import datetime
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from usuarios.models import Perfil

def es_staff(user):
    if not user.is_authenticated:
        return False
    try:
        perfil = Perfil.objects.get(usuario=user)
        return perfil.rol and perfil.rol.nombre in ['Administrador', 'Mecánico', 'Recepcionista']
    except (Perfil.DoesNotExist, AttributeError):
        return False

# Vistas para vehículos
@login_required
def lista_vehiculos(request):
    vehiculos = Vehiculo.objects.filter(propietario=request.user)
    return render(request, 'citas/lista_vehiculos.html', {'vehiculos': vehiculos})

@login_required
def agregar_vehiculo(request):
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.propietario = request.user
            vehiculo.save()
            messages.success(request, 'Vehículo agregado correctamente.')
            return redirect('lista_vehiculos')
    else:
        form = VehiculoForm()
    
    return render(request, 'citas/agregar_vehiculo.html', {'form': form})

@login_required
def editar_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, propietario=request.user)
    
    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehículo actualizado correctamente.')
            return redirect('lista_vehiculos')
    else:
        form = VehiculoForm(instance=vehiculo)
    
    return render(request, 'citas/editar_vehiculo.html', {'form': form, 'vehiculo': vehiculo})

@login_required
def eliminar_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, propietario=request.user)
    
    if request.method == 'POST':
        vehiculo.delete()
        messages.success(request, 'Vehículo eliminado correctamente.')
        return redirect('lista_vehiculos')
    
    return render(request, 'citas/eliminar_vehiculo.html', {'vehiculo': vehiculo})

# Vistas para citas
@login_required
def mis_citas(request):
    # Obtener las citas del usuario actual
    citas = Cita.objects.filter(cliente=request.user).order_by('-fecha', 'hora_inicio')
    return render(request, 'citas/mis_citas.html', {'citas': citas})

@login_required
def seleccionar_fecha_hora(request):
    """Vista para seleccionar la fecha y ver horarios disponibles"""
    if request.method == 'POST':
        form = FechaHoraDisponibleForm(request.POST)
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
            categoria = form.cleaned_data['categoria_servicio']
            
            # Redirigir a la página para crear la cita
            return redirect('nueva_cita', fecha=fecha.strftime('%Y-%m-%d'), categoria=categoria)
    else:
        form = FechaHoraDisponibleForm()
    
    return render(request, 'citas/seleccionar_fecha_hora.html', {'form': form})

@login_required
def horas_disponibles(request):
    """API para obtener horas disponibles en una fecha específica"""
    fecha_str = request.GET.get('fecha')
    categoria = request.GET.get('categoria')
    
    if not fecha_str or not categoria:
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)
    
    try:
        fecha = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)
    
    # Horario de atención (8:00 AM a 5:00 PM)
    inicio_jornada = datetime.time(8, 0)  # 8:00 AM
    fin_jornada = datetime.time(17, 0)    # 5:00 PM
    
    # Intervalo de citas (cada 30 minutos)
    intervalo_minutos = 30
    
    # Generar todos los horarios posibles
    horarios_posibles = []
    hora_actual = inicio_jornada
    while hora_actual < fin_jornada:
        horarios_posibles.append(hora_actual)
        # Sumar intervalo_minutos
        hora_dt = datetime.datetime.combine(datetime.date.today(), hora_actual)
        hora_dt = hora_dt + datetime.timedelta(minutes=intervalo_minutos)
        hora_actual = hora_dt.time()
    
    # Obtener citas existentes en esa fecha
    citas_existentes = Cita.objects.filter(
        fecha=fecha,
        estado__in=['PENDIENTE', 'CONFIRMADA'],
        servicio__categoria=categoria
    )
    
    # Marcar horarios ocupados
    horarios_ocupados = set()
    for cita in citas_existentes:
        hora_inicio_cita = cita.hora_inicio
        hora_fin_cita = cita.hora_fin
        
        # Marcar como ocupados todos los horarios que se solapan con esta cita
        for horario in horarios_posibles:
            horario_dt = datetime.datetime.combine(datetime.date.today(), horario)
            horario_fin_dt = horario_dt + datetime.timedelta(minutes=intervalo_minutos)
            horario_fin = horario_fin_dt.time()
            
            if hora_inicio_cita < horario_fin and hora_fin_cita > horario:
                horarios_ocupados.add(horario)
    
    # Filtrar solo horarios disponibles
    horarios_disponibles = [h for h in horarios_posibles if h not in horarios_ocupados]
    
    # Convertir a formato JSON compatible
    horarios_json = [{'hora': h.strftime('%H:%M'), 'valor': h.strftime('%H:%M')} 
                     for h in horarios_disponibles]
    
    return JsonResponse({'horarios': horarios_json})

@login_required
def nueva_cita(request, fecha, categoria):
    """Vista para crear una nueva cita"""
    try:
        fecha_obj = datetime.datetime.strptime(fecha, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Formato de fecha inválido.')
        return redirect('seleccionar_fecha_hora')
    
    if request.method == 'POST':
        form = CitaForm(request.POST, user=request.user, categoria=categoria)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.cliente = request.user
            
            # Calcular la hora de fin basada en la duración del servicio
            inicio_dt = datetime.datetime.combine(
                fecha_obj, 
                cita.hora_inicio
            )
            fin_dt = inicio_dt + datetime.timedelta(minutes=cita.servicio.duracion)
            cita.hora_fin = fin_dt.time()
            
            try:
                cita.save()
                
                # Crear notificación de confirmación
                Notificacion.objects.create(
                    cita=cita,
                    tipo='CONFIRMACION',
                    mensaje=f'Su cita para {cita.servicio.nombre} ha sido agendada para el {cita.fecha} a las {cita.hora_inicio}.',
                    enviado=False
                )
                
                # Enviar email de confirmación
                try:
                    send_mail(
                        f'Confirmación de Cita - {cita.servicio.nombre}',
                        f'Su cita para {cita.servicio.nombre} ha sido agendada para el {cita.fecha} a las {cita.hora_inicio}.',
                        settings.EMAIL_HOST_USER,
                        [request.user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Error al enviar email: {e}")
                
                messages.success(request, 'Cita agendada correctamente.')
                return redirect('mis_citas')
            except ValidationError as e:
                messages.error(request, e)
    else:
        # Inicializar el formulario con la fecha seleccionada
        form = CitaForm(
            initial={'fecha': fecha_obj},
            user=request.user,
            categoria=categoria
        )
    
    context = {
        'form': form,
        'fecha': fecha_obj,
        'categoria': dict(TipoServicio.CATEGORIAS).get(categoria, categoria)
    }
    return render(request, 'citas/nueva_cita.html', context)

@login_required
def detalle_cita(request, cita_id):
    """Vista para ver detalles de una cita"""
    cita = get_object_or_404(Cita, id=cita_id)
    
    # Verificar que el usuario es el dueño de la cita o es staff
    if cita.cliente != request.user and not es_staff(request.user):
        messages.error(request, 'No tienes permiso para ver esta cita.')
        return redirect('mis_citas')
    
    return render(request, 'citas/detalle_cita.html', {'cita': cita})

@login_required
def cancelar_cita(request, cita_id):
    """Vista para cancelar una cita"""
    cita = get_object_or_404(Cita, id=cita_id, cliente=request.user)
    
    # Solo se pueden cancelar citas pendientes o confirmadas
    if cita.estado not in ['PENDIENTE', 'CONFIRMADA']:
        messages.error(request, 'No se puede cancelar una cita que ya ha sido completada o cancelada.')
        return redirect('mis_citas')
    
    if request.method == 'POST':
        cita.estado = 'CANCELADA'
        cita.save()
        
        # Crear notificación
        Notificacion.objects.create(
            cita=cita,
            tipo='CAMBIO_ESTADO',
            mensaje=f'Su cita para {cita.servicio.nombre} del {cita.fecha} a las {cita.hora_inicio} ha sido cancelada.',
            enviado=False
        )
        
        messages.success(request, 'Cita cancelada correctamente.')
        return redirect('mis_citas')
    
    return render(request, 'citas/cancelar_cita.html', {'cita': cita})

# Vistas para personal (admin, mecánicos, recepcionistas)
@login_required
def calendario_citas(request):
    """Vista de calendario para ver todas las citas"""
    if not es_staff(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    # Filtrar por fecha (si se proporciona)
    fecha = request.GET.get('fecha')
    categoria = request.GET.get('categoria')
    
    citas = Cita.objects.all().order_by('fecha', 'hora_inicio')
    
    if fecha:
        try:
            fecha_obj = datetime.datetime.strptime(fecha, '%Y-%m-%d').date()
            citas = citas.filter(fecha=fecha_obj)
        except ValueError:
            messages.error(request, 'Formato de fecha inválido.')
    
    if categoria:
        citas = citas.filter(servicio__categoria=categoria)
    
    return render(request, 'citas/calendario_citas.html', {
        'citas': citas,
        'fecha_filtro': fecha,
        'categoria_filtro': categoria,
    })

@login_required
def gestionar_cita(request, cita_id):
    """Vista para que el personal gestione una cita"""
    if not es_staff(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    cita = get_object_or_404(Cita, id=cita_id)
    
    if request.method == 'POST':
        form = GestionCitaForm(request.POST, instance=cita)
        if form.is_valid():
            estado_anterior = cita.estado
            cita = form.save()
            
            # Si cambió el estado, crear notificación
            if estado_anterior != cita.estado:
                Notificacion.objects.create(
                    cita=cita,
                    tipo='CAMBIO_ESTADO',
                    mensaje=f'Su cita para {cita.servicio.nombre} ha cambiado de estado a {cita.get_estado_display()}.',
                    enviado=False
                )
            
            messages.success(request, 'Cita actualizada correctamente.')
            return redirect('calendario_citas')
    else:
        form = GestionCitaForm(instance=cita)
    
    return render(request, 'citas/gestionar_cita.html', {'form': form, 'cita': cita})

# Vistas para tipos de servicio
@login_required
def lista_servicios(request):
    """Vista para listar todos los tipos de servicio"""
    if not es_staff(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    servicios = TipoServicio.objects.all()
    return render(request, 'citas/lista_servicios.html', {'servicios': servicios})

@login_required
def agregar_servicio(request):
    """Vista para agregar un nuevo tipo de servicio"""
    if not es_staff(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        duracion = request.POST.get('duracion')
        precio = request.POST.get('precio')
        categoria = request.POST.get('categoria')
        
        try:
            TipoServicio.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                duracion=duracion,
                precio=precio,
                categoria=categoria
            )
            messages.success(request, 'Servicio agregado correctamente.')
            return redirect('lista_servicios')
        except Exception as e:
            messages.error(request, f'Error al agregar servicio: {e}')
    
    return render(request, 'citas/agregar_servicio.html', {'categorias': TipoServicio.CATEGORIAS})

@login_required
def editar_servicio(request, servicio_id):
    """Vista para editar un tipo de servicio"""
    if not es_staff(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    servicio = get_object_or_404(TipoServicio, id=servicio_id)
    
    if request.method == 'POST':
        servicio.nombre = request.POST.get('nombre')
        servicio.descripcion = request.POST.get('descripcion')
        servicio.duracion = request.POST.get('duracion')
        servicio.precio = request.POST.get('precio')
        servicio.categoria = request.POST.get('categoria')
        
        try:
            servicio.save()
            messages.success(request, 'Servicio actualizado correctamente.')
            return redirect('lista_servicios')
        except Exception as e:
            messages.error(request, f'Error al actualizar servicio: {e}')
    
    return render(request, 'citas/editar_servicio.html', {
        'servicio': servicio,
        'categorias': TipoServicio.CATEGORIAS
    })

@login_required
def eliminar_servicio(request, servicio_id):
    """Vista para eliminar un tipo de servicio"""
    if not es_staff(request.user):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    servicio = get_object_or_404(TipoServicio, id=servicio_id)
    
    if request.method == 'POST':
        servicio.delete()
        messages.success(request, 'Servicio eliminado correctamente.')
        return redirect('lista_servicios')
    
    return render(request, 'citas/eliminar_servicio.html', {'servicio': servicio})