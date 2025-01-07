from django.db import models
from datetime import datetime


class CSVFile(models.Model):
    file = models.FileField(upload_to='csv_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class WithoutFecha_F(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset().filter(FECHA_F__isnull=True)
        )


class CSVData(models.Model):
    Proyecto = models.IntegerField()
    OM = models.IntegerField()
    Fecha_Creacion = models.DateField(null=True, blank=True)
    Peticionario = models.CharField(max_length=20)
    Factibilidad = models.IntegerField()
    Plazo = models.DateField(null=True, blank=True)
    Cerrado = models.BooleanField()
    Fecha_Cierre = models.DateField(null=True, blank=True)
    Tarea = models.IntegerField()
    Usuario = models.CharField(max_length=20)
    FECHA_I = models.DateField(null=True, blank=True)
    Fecha_Fin_Prevista = models.DateField(null=True, blank=True)
    FECHA_F = models.DateField(null=True, blank=True)
    PCP_Lock_bit = models.BooleanField()
    PCP_Lock = models.CharField(max_length=10)
    Unlocking_Remarks = models.CharField(max_length=100, null=True, blank=True)
    NUM_PEDIDO = models.IntegerField()
    Fecha_Cliente = models.DateField(null=True, blank=True)
    FECHA_ENTREGA = models.DateField(null=True, blank=True)
    ESTADO = models.CharField(max_length=100)
    PROG_MRP = models.CharField(max_length=8)
    QUANTITY = models.IntegerField(null=True, blank=True)
    Seccion = models.CharField(max_length=100, null=True, blank=True)
    FECHA_PREVISTA_MRP = models.DateField(null=True, blank=True)
    ProjectDescription = models.CharField(max_length=500, null=True, blank=True)

    objects = models.Manager()
    without_F = WithoutFecha_F()

    def save(self, *args, **kwargs):
        date_fields = [
            'Fecha_Creacion', 'Fecha_Cierre', 'FECHA_I', 'FECHA_F',
            'Fecha_Cliente', 'FECHA_ENTREGA', 'FECHA_PREVISTA_MRP'
        ]
        for field in date_fields:
            value = getattr(self, field)
            if value and isinstance(value, str):
                try:
                    setattr(self, field, datetime.strptime(value, '%d/%m/%Y').date())
                except ValueError:
                    raise ValueError(f"Invalid date format for field {field}: {value}")
        super().save(*args, **kwargs)


class Report(models.Model):
    Fecha_Fin_Prevista = models.DateField(null=True, blank=True)
    OM = models.IntegerField()
    Peticionario = models.CharField(max_length=20)
    FECHA_ENTREGA = models.DateField()
    FECHA_PREVISTA_MRP = models.DateField(null=True, blank=True)
    Seccion = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.OM} - {self.Peticionario}"
