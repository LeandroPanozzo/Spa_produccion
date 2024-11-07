from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response as httpResponce
from rest_framework.decorators import action
from django.utils import timezone
from .models import Profile, Post
#from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
from .serializer import ProfileSerializer, UserUpdateSerializer, PostSerializer, PaymentSerializer, PaymentTypeSerializer, RegisterSerializer, UserDetailSerializer, CustomTokenObtainPairSerializer, QuerySerializer, ResponseSerializer, AppointmentSerializer, ServiceSerializer, AnnouncementSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from .permissions import IsStaffAndReadOrEditOnly, IsStaff, IsOwner, IsOwnerOrIsSecretary, IsProfessional
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Query, Respuesta, Appointment, Service, Announcement, User, Payment, PaymentType


from functools import wraps

class UserEditViewSet(viewsets.ModelViewSet):
    
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Limita la vista a que solo se acceda al usuario autenticado
        return User.objects.filter(id=self.request.user.id)
    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()  # Guarda los cambios
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaymentListViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden acceder a la vista

    def get_queryset(self):
        user = self.request.user

        # Verifica si el usuario es secretario
        if (not user.is_secretary and not user.is_owner):
            return Payment.objects.none()  # Retorna una queryset vacía si no es secretario

        # Obtener los parámetros de la URL para filtrar entre fechas
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        queryset = Payment.objects.all()

        # Si ambos parámetros de fecha están presentes, filtrar entre esas fechas
        if start_date and end_date:
            try:
                start_date = parse_datetime(start_date)  # Cambiado a parse_datetime
                end_date = parse_datetime(end_date)      # Cambiado a parse_datetime

                if start_date and end_date:
                    # Convertir a "aware" usando la zona horaria local
                    start_date = timezone.make_aware(start_date)
                    end_date = timezone.make_aware(end_date) + timedelta(days=1)

                    queryset = queryset.filter(payment_date__range=[start_date, end_date])
            except (TypeError, ValueError):
                return queryset.none()

        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        payment_data = []
        for payment in serializer.data:
            appointment_id = payment['appointment']
            payment_type_id = payment['payment_type']
            try:
                payment_type = PaymentType.objects.get(id=payment_type_id)
                appointment = Appointment.objects.get(id=appointment_id)
                client = appointment.client
                payment['client_first_name'] = client.first_name
                payment['client_last_name'] = client.last_name
                payment['payment_type'] = payment_type.name
            except Appointment.DoesNotExist:
                payment['client_first_name'] = ''
                payment['client_last_name'] = ''
                payment['payment_type'] = ''
            payment_data.append(payment)

        return Response(payment_data, status=status.HTTP_200_OK)

class ProfessionalAppointmentsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    
    def get_queryset(self):
        user = self.request.user
        if user.is_professional:
            # Obtener la fecha actual
            today = timezone.now().date()
            # Retornar las citas del profesional autenticado desde la fecha actual, ordenadas por fecha y hora
            return Appointment.objects.filter(professional=user, appointment_date__gte=today).order_by('appointment_date')
        return Appointment.objects.none()  # Si no es profesional, no retorna nada

from django.utils.cache import add_never_cache_headers

class PaymentTypeView(viewsets.ViewSet):
    queryset = PaymentType.objects.all()
    serializer_class = PaymentTypeSerializer
    
    def list(self, request):
        queryset = self.queryset
        serializer = self.serializer_class(queryset, many=True)
        response = Response(serializer.data)
        add_never_cache_headers(response)  # Desactivar caché para esta respuesta
        return response
    
def send_invoice_after_creation(func):
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        response = func(self, request, *args, **kwargs)  # Llama a la función original

        # Si el pago fue creado correctamente, envía la factura
        if response.status_code == status.HTTP_201_CREATED:
            appointment_id = request.data.get('appointment')
            try:
                appointment = Appointment.objects.get(id=appointment_id)
                send_invoice(appointment)  # Llama a la función para enviar el correo
            except Appointment.DoesNotExist:
                pass  # Manejo si no se encuentra la cita, puedes logearlo si es necesario

        return response
    return wrapper

from decimal import Decimal



class PaymentCreateView(viewsets.ViewSet):
    
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        queryset = self.queryset
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)
    
    @send_invoice_after_creation
    def create(self, request):
        
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                appointment = Appointment.objects.get(id=request.data['appointment'])
                if not appointment.services.exists():
                    return Response({"error": "La cita no tiene servicios asociados"}, status=status.HTTP_400_BAD_REQUEST)
                
                discount = Decimal(request.data.get('discount', 0))
                
                total_payment = sum(service.price for service in appointment.services.all()) - (Decimal('1') - discount)
                
                
                serializer.save(total_payment=total_payment)
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Appointment.DoesNotExist:
                return Response({"error": "La cita no existe"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientsByProfessionalViewSet(viewsets.ViewSet):
    """
    Vista para mostrar los clientes atendidos por cada profesional,
    ordenados por horario.
    Solo puede acceder el usuario con el rol `is_owner`.
    """
    permission_classes = [IsAuthenticated, IsOwner | IsProfessional]

    def list(self, request):
        """
        Obtiene los clientes atendidos por cada profesional,
        agrupados por profesional y ordenados por horario.
        """
        professional_id = request.query_params.get('professional_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Filtro base
        appointments = Appointment.objects.all().select_related('client', 'professional').prefetch_related('services')

        # Si se proporcionan las fechas, convertirlas a "aware"
        if start_date and end_date:
            try:
                # Usamos parse_datetime para convertir las fechas de las query params
                start_date = parse_datetime(start_date)
                end_date = parse_datetime(end_date)

                if start_date and end_date:
                    # Convertir las fechas naive a aware usando la zona horaria local
                    start_date = timezone.make_aware(start_date)
                    # Aumentar un día para incluir el final del día en end_date
                    end_date = timezone.make_aware(end_date) + timedelta(days=1)

                    appointments = appointments.filter(appointment_date__range=[start_date, end_date])
            except (TypeError, ValueError):
                return Response({"detail": "Invalid date format."}, status=status.HTTP_400_BAD_REQUEST)

        # Filtro por profesional si se proporciona
        if professional_id:
            appointments = appointments.filter(professional_id=professional_id)

        appointments = appointments.order_by('appointment_date')
        
        grouped_appointments = {}

        for appointment in appointments:
            professional_name = f"{appointment.professional.first_name} {appointment.professional.last_name}"
            if professional_name not in grouped_appointments:
                grouped_appointments[professional_name] = []
            
            # Obtenemos los nombres de los servicios asociados a la cita
            services = [service.name for service in appointment.services.all()]

            grouped_appointments[professional_name].append({
                "client_first_name": appointment.client.first_name,
                "client_last_name": appointment.client.last_name,
                "appointment_date": appointment.appointment_date.strftime("%Y-%m-%d %H:%M"),
                "services": services  # Agregamos los servicios aquí
            })

        return Response(grouped_appointments)

class ClientsByDayViewSet(viewsets.ViewSet):
    """
    Vista para mostrar los clientes a atender por día.
    Solo puede acceder el usuario con el rol `is_owner`.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsOwner]  # Solo usuarios autenticados y `is_owner` pueden acceder
    
    def get_queryset(self):
        """
        Solo usuarios con is_owner pueden ver la información.
        """
        return Appointment.objects.all().order_by('appointment_date')

    @action(detail=False, methods=['get'])
    def grouped_by_date(self, request):
        """
        Agrupa las citas por fecha y devuelve una estructura con las citas por fecha.
        """
        appointments = self.get_queryset()
        
        grouped_appointments = {}
        for appointment in appointments:
            date_str = appointment.appointment_date.strftime("%Y-%m-%d")
            if date_str not in grouped_appointments:
                grouped_appointments[date_str] = []

            # Aquí se cargan todos los nombres de los servicios de la cita
            services_names = [service.name for service in appointment.services.all()]
            
            grouped_appointments[date_str].append({
                "client": appointment.client.username,
                "first_name": appointment.client.first_name,
                "last_name": appointment.client.last_name,
                "services": services_names  # Cambiamos 'service' por 'services' para reflejar múltiples
            })

        return Response(grouped_appointments)
    
class ProfessionalViewSet(viewsets.ModelViewSet):
    """
    Vista para listar los usuarios que son profesionales.
    """
    queryset = User.objects.filter(is_professional=True)
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]  # Ajusta según sea necesario

    def get_queryset(self):
        return self.queryset
    def list(self, request, *args, **kwargs):
        # Llamar al método original para obtener la lista de profesionales
        response = super().list(request, *args, **kwargs)
        
        # Agregar los encabezados de no caché a la respuesta
        #add_never_cache_headers(response)
        
        return response

class ClientViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def update(self, request, *args, **kwargs):
        # Método personalizado para manejar la actualización de permisos
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    
        
from django.core.exceptions import PermissionDenied

class AnnouncementView(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer

    def get_queryset(self):
        return Announcement.objects.order_by('-created_at')  # Orden descendente por created_at
    
    def perform_create(self, serializer):
        # Verificar si el usuario es propietario o secretario antes de crear
        if self.request.user.is_owner or self.request.user.is_secretary:
            serializer.save(user=self.request.user)
        else:
            # Si no tiene permisos, devolver un error
            raise PermissionDenied("No tienes permiso para crear anuncios.")

    def destroy(self, request, *args, **kwargs):
        # Verificar si el usuario es propietario o secretario antes de eliminar
        if request.user.is_owner or request.user.is_secretary:
            return super().destroy(request, *args, **kwargs)
        else:
            # Si no tiene permisos, devolver un error
            return Response({"detail": "No tienes permiso para eliminar anuncios."}, status=status.HTTP_403_FORBIDDEN)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsStaffAndReadOrEditOnly, IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(client=self.request.user)
        
    def get_queryset(self):
        if self.request.user.is_owner or self.request.user.is_secretary:
            # Empleados ven todos los appointments
            return Appointment.objects.all()
            
        if self.request.user.is_professional:
            # Empleados ven todos los appointments
            return Appointment.objects.filter(
                professional=self.request.user
            ) | Appointment.objects.filter(client=self.request.user)
            
        else:
            # Usuarios normales ven solo sus appointments
            return Appointment.objects.filter(client=self.request.user)

class QueryViewSet(viewsets.ModelViewSet):
    queryset = Query.objects.all()
    serializer_class = QuerySerializer
    permission_classes = [IsAuthenticated, IsStaffAndReadOrEditOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    def get_queryset(self):
        
        if self.request.user.is_secretary or self.request.user.is_owner:
            # Empleados ven todos los appointments
            return Query.objects.all()
        else:
            # Usuarios normales ven solo sus appointments
            return Query.objects.filter(user=self.request.user)

class ResponseViewSet(viewsets.ModelViewSet):
    queryset = Respuesta.objects.all()
    serializer_class = ResponseSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    def get_queryset(self):
        
        if self.request.user.is_secretary or self.request.user.is_owner:
            # Empleados ven todos los appointments
            return Respuesta.objects.all()
        else:
            # Usuarios normales ven solo sus appointments
            return Respuesta.objects.filter(user=self.request.user)

class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()

    @action(detail=True, methods=['delete'])
    def delete_profile(self, request, pk=None):
        profile = get_object_or_404(Profile, pk=pk)
        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-fecha_posteo')
    serializer_class = PostSerializer
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_authenticated:
            # Usuario autenticado, asignar `autor` y dejar `alias` como `null`
            serializer.save(autor=user, alias=None)
        else:
            # Usuario no autenticado, asignar `alias` y dejar `autor` como `null`
            alias = self.request.data.get('alias', None)
            serializer.save(autor=None, alias=alias)
            
from rest_framework.exceptions import ValidationError

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": RegisterSerializer(user, context=self.get_serializer_context()).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        else:
            # Aquí devolvemos los errores de validación del serializer
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
# En views.py
from rest_framework import generics
#from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated

class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
from rest_framework.decorators import api_view
from django.http import FileResponse

from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

def generar_factura(appointment):
    archivo_pdf = f"factura_{appointment.id}.pdf"
    c = canvas.Canvas(archivo_pdf, pagesize=A4)
    ancho, alto = A4

    margen_izquierdo = 2 * cm
    margen_superior = alto - 2 * cm

    # Encabezado "ORIGINAL"
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(ancho / 2.0, alto - 1.5 * cm, "ORIGINAL")

    # Cuadro para "Factura C" en el centro
    c.setFont("Helvetica-Bold", 18)
    c.rect(margen_izquierdo + 3.5 * cm, margen_superior - 70, 5 * cm, 50)  # Cuadro alrededor de "C"
    c.drawString(margen_izquierdo + 5.5 * cm, margen_superior - 40, "B")  # Letra B

    # Detalles de la factura a la derecha
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margen_izquierdo + 250, margen_superior - 20, "FACTURA B")
    c.setFont("Helvetica", 10)
    c.drawString(margen_izquierdo + 250, margen_superior - 40, "Punto de Venta: 0002")
    c.drawString(margen_izquierdo + 250, margen_superior - 60, f"Comprobante Nro: {appointment.payment.id}")
    c.drawString(margen_izquierdo + 250, margen_superior - 80, f"Fecha de Emisión: {datetime.now().strftime('%d/%m/%Y')}")

    # Línea divisoria
    c.line(margen_izquierdo, margen_superior - 100, ancho - margen_izquierdo, margen_superior - 100)

    # Detalles del SPA (razón social y domicilio comercial)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margen_izquierdo, margen_superior - 120, "Razón Social:    ")
    c.setFont("Helvetica", 10)
    c.drawString(margen_izquierdo + 90, margen_superior - 120, "SPA Sentirse Bien   ")
    c.drawString(margen_izquierdo, margen_superior - 140, "Domicilio Comercial:    ")
    c.drawString(margen_izquierdo + 90, margen_superior - 140, " Calle Falsa 123, Ciudad   ")

    # Condición frente al IVA
    c.drawString(margen_izquierdo, margen_superior - 160, "Condición frente al IVA:   ")
    c.drawString(margen_izquierdo + 150, margen_superior - 160, "Responsable Inscripto   ")

    # Datos del cliente
    c.drawString(margen_izquierdo, margen_superior - 200, "CUIT del Cliente:   ")
    c.drawString(margen_izquierdo + 150, margen_superior - 200, f"CUIT: {appointment.client.cuit if appointment.client.cuit else 'Sin CUIT'}")
    c.drawString(margen_izquierdo, margen_superior - 220, "Condición IVA del Cliente:  ")
    c.drawString(margen_izquierdo + 150, margen_superior - 220, "Consumidor Final   ")

    # Segunda Línea divisoria
    c.line(margen_izquierdo, margen_superior - 240, ancho - margen_izquierdo, margen_superior - 240)

    # Título de la tabla de productos/servicios
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margen_izquierdo, margen_superior - 260, "Detalle de los Servicios")

    # Tabla de productos/servicios
    data = [['Código', 'Producto / Servicio', 'Cantidad', 'U. Medida', 'Precio Unit.']]
    
    # Agregar los servicios a la tabla
    for service in appointment.services.all():
        data.append([service.id, service.name, '1.00', 'unidades', f'${service.price:.2f}'])

    # Calcular la altura de la tabla en base al número de filas
    num_rows = len(data)
    table_height = num_rows * 0.5 * cm  # Ajusta el factor de altura según el tamaño de fuente
    table_start_y = margen_superior - 320 - table_height  # Calcula la posición inicial de la tabla

    tabla = Table(data, colWidths=[2 * cm, 6 * cm, 2 * cm, 2 * cm, 3 * cm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    tabla.wrapOn(c, ancho, alto)
    tabla.drawOn(c, margen_izquierdo, table_start_y)

    # Subtotales y total
    subtotal = sum(service.price for service in appointment.services.all())
    total = subtotal * (Decimal('1') - Decimal(appointment.payment.discount))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margen_izquierdo + 350, table_start_y - 20, f"Subtotal: ${subtotal:.2f}")
    c.drawString(margen_izquierdo + 350, table_start_y - 40, f"Total: ${total:.2f}")
    c.drawString(margen_izquierdo + 350, table_start_y - 60, f"Descuento: {appointment.payment.discount * 100:.2f} %")

    # Tercera línea divisoria
    c.line(margen_izquierdo, table_start_y - 70, ancho - margen_izquierdo, table_start_y - 70)

    # Pie de página
    c.setFont("Helvetica", 8)
    c.drawString(margen_izquierdo, 1 * cm, "Este comprobante es una Factura B. Autorizado por la AFIP.")
    c.drawString(margen_izquierdo, 0.5 * cm, "Código de Autorización: XXXXXXXXXXXXX")

    c.showPage()
    c.save()

# Vista para descargar el PDF
@api_view(['GET'])
def download_invoice(request, appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        generar_factura(appointment)

        # Devolver el archivo PDF generado
        return FileResponse(open(f"factura_{appointment.id}.pdf", "rb"), content_type='application/pdf', as_attachment=True, filename=f"factura_{appointment.id}.pdf")

    except Appointment.DoesNotExist:
        return Response({"detail": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
from django.core.mail import EmailMessage
from django.conf import settings

def send_invoice(appointment):
    # Generar la factura
    generar_factura(appointment)

    # Preparar la información adicional
    fecha_hora = appointment.appointment_date.strftime("%d/%m/%Y %H:%M")  # Formato de fecha y hora
    servicios = ", ".join([service.name for service in appointment.services.all()])  # Listar los nombres de los servicios
    profesional_nombre = f"{appointment.professional.first_name} {appointment.professional.last_name}"  # Nombre del profesional

    # Cuerpo del correo
    body = (
        f"Estimado/a {appointment.client.first_name},\n\n"
        f"Adjuntamos su factura por el servicio solicitado.\n\n"
        f"Detalles de la cita:\n"
        f"Fecha y Hora: {fecha_hora}\n"
        f"Servicios: {servicios}\n"
        f"Profesional: {profesional_nombre}\n\n"
        "IMPORTANTE: Recuerde que debe presentarse con la factura adjunta, a su reserva\n"
        "Gracias por confiar en nosotros."
    )

    # Preparar el correo
    email = EmailMessage(
        subject=f"Factura para la cita #{appointment.id}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[appointment.client.email],  # Asegúrate de que el cliente tenga un email asociado
    )

    # Adjuntar el PDF
    archivo_pdf = f"factura_{appointment.id}.pdf"
    email.attach_file(archivo_pdf)

    # Enviar el correo
    email.send()
    


