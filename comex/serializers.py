from rest_framework.serializers import ModelSerializer, Serializer, EmailField, CharField
from rest_framework import serializers
from .models import Usuario, Categoria, Producto, Media, Despacho


class UsuarioSerializer(ModelSerializer):
    class Meta:
        model = Usuario
        exclude = ["is_staff", "is_superuser", "is_active", "user_permissions", "last_login", "groups"]
        extra_kwargs = {
            "password": {
                "write_only": True
            }
        }


class LoginSerializer(Serializer):
    correo = EmailField(required=True)
    password = CharField(required=True)


class CategoriaSerializer(ModelSerializer):
    class Meta:
        model = Categoria
        exclude = ["eliminado"]


class ProductoSerializer(ModelSerializer):
    url = serializers.CharField(read_only=True)

    class Meta:
        model = Producto
        exclude = ["eliminado"]
        extra_kwargs = {
            "media": {"write_only": True}
        }


class ProductoDetalleSerializer(ModelSerializer):
    class Meta:
        model = Producto
        exclude = ["eliminado"]
        depth = 1


class GenerarUrlAWSSerializer(Serializer):
    contentTypeValidas = ["image/jpeg", "image/png", "application/pdf"]
    extensionesValidas = ["png", "jpg", "jpeg", "pdf"]

    fileName = serializers.CharField(trim_whitespace=True, max_length=100, required=True)
    ext = serializers.ChoiceField(
        choices=extensionesValidas,
        error_messages={
            "invalid_choice": "Ext invalida, use 'png', 'jpg', 'jpeg' o 'pdf'"
        },
        required=True,
    )
    contentType = serializers.ChoiceField(choices=contentTypeValidas, required=True)
    size = serializers.FloatField(max_value=10 * 1024 * 1024, min_value=5 * 1024, required=True)
    folder = serializers.CharField(required=False)


class MediaSerializer(ModelSerializer):
    class Meta:
        model = Media
        fields = "__all__"


class DespachoSerializer(ModelSerializer):
    class Meta:
        model = Despacho
        exclude = ["eliminado"]
