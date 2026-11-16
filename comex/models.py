from django.db import models
from uuid import uuid4
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class ManejadorUsuario(BaseUserManager):
    def create_superuser(self, nombre, correo, password):
        if not correo or len(correo) == 0:
            raise ValueError("El correo es obligatorio")

        correoNormalizado = self.normalize_email(correo)
        nuevoUsuario = self.model(correo=correoNormalizado, nombre=nombre)
        nuevoUsuario.set_password(password)

        nuevoUsuario.is_superuser = True
        nuevoUsuario.is_staff = True

        nuevoUsuario.save()


class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid4)
    nombre = models.TextField()
    apellidos = models.TextField(null=True)
    correo = models.TextField(unique=True)
    password = models.TextField()

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "correo"
    REQUIRED_FIELDS = ["nombre"]

    objects = ManejadorUsuario()

    class Meta:
        db_table = "usuarios"


class Categoria(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    nombre = models.CharField(max_length=100, null=False)
    habilitado = models.BooleanField(default=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        db_table = "categorias"


class Media(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    nombre = models.CharField(max_length=100, null=False)
    ext = models.CharField(max_length=100, null=False)
    ruta = models.CharField(max_length=200, null=False)
    mimeType = models.CharField(db_column="mime_type", max_length=100, null=False)
    habilitado = models.BooleanField(default=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        db_table = "medias"


class Producto(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    nombre = models.CharField(max_length=200, null=False)
    calibre = models.CharField(max_length=100, null=False)
    stock = models.IntegerField(default=0, null=False)
    habilitado = models.BooleanField(default=True)
    eliminado = models.BooleanField(default=False)

    categoria = models.ForeignKey(to=Categoria, on_delete=models.PROTECT, db_column="categoria_id")
    media = models.ForeignKey(to=Media, on_delete=models.PROTECT, db_column="media_id", null=True)

    class Meta:
        db_table = "productos"


ESTADO_DESPACHOS = {
    "CONFIRMADO": "CONFIRMADO",
    "CANCELADO": "CANCELADO",
    "PENDIENTE": "PENDIENTE",
}


class Despacho(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    cliente = models.TextField(null=False)
    paisDestino = models.TextField(db_column="pais_destino", null=False)
    cantidadCajas = models.IntegerField(db_column="cantidad_cajas", null=False)
    estado = models.TextField(choices=ESTADO_DESPACHOS, default=ESTADO_DESPACHOS["CONFIRMADO"])
    eliminado = models.BooleanField(default=False)

    producto = models.ForeignKey(to=Producto, on_delete=models.PROTECT, db_column="producto_id")
    usuario = models.ForeignKey(to=Usuario, on_delete=models.PROTECT, db_column="usuario_id")

    class Meta:
        db_table = "despachos"
