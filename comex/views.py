from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from .models import Usuario, Categoria, Producto, Media, Despacho
from .serializers import (
    UsuarioSerializer,
    LoginSerializer,
    CategoriaSerializer,
    ProductoSerializer,
    ProductoDetalleSerializer,
    GenerarUrlAWSSerializer,
    MediaSerializer,
    DespachoSerializer,
)
from .pagination import PaginacionEstandar
from uuid import UUID, uuid4
from boto3 import client
from os import getenv
from urllib.parse import unquote


@api_view(http_method_names=["POST"])
def registroUsuario(request: Request):
    serializador = UsuarioSerializer(data=request.data)

    if serializador.is_valid():
        nombre = serializador.validated_data.get("nombre")
        apellidos = serializador.validated_data.get("apellidos")
        correo = serializador.validated_data.get("correo")
        password = serializador.validated_data.get("password")

        nuevoUsuario = Usuario(nombre=nombre, apellidos=apellidos, correo=correo)
        nuevoUsuario.set_password(password)
        nuevoUsuario.save()

        return Response(data={
            "message": "Usuario registrado exitosamente"
        }, status=status.HTTP_201_CREATED)
    else:
        return Response(data={
            "message": "Error al crear el usuario",
            "content": serializador.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(http_method_names=["POST"])
def loginManual(request: Request):
    serializador = LoginSerializer(data=request.data)

    if serializador.is_valid():
        correo = serializador.validated_data.get("correo")
        password = serializador.validated_data.get("password")
        usuarioEncontrado = Usuario.objects.filter(correo=correo).first()

        if not usuarioEncontrado:
            return Response(data={
                "message": "El usuario no existe"
            }, status=status.HTTP_400_BAD_REQUEST)

        esLaPassword = usuarioEncontrado.check_password(password)
        if esLaPassword:
            token = RefreshToken.for_user(usuarioEncontrado)
            token2 = AccessToken.for_user(usuarioEncontrado)
            return Response(data={
                "content": {
                    "accessToken": str(token.access_token),
                },
                "token": str(token2),
            })
        else:
            return Response(data={
                "message": "Credenciales invalidas"
            }, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(data={
            "message": "Error al hacer el login",
            "content": serializador.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(http_method_names=["GET"])
@permission_classes([IsAuthenticated])
def perfilUsuario(request: Request):
    usuarioActual = request.user
    serializador = UsuarioSerializer(instance=usuarioActual)
    return Response(data={
        "content": serializador.data
    })


class CategoriasView(APIView):
    def get(self, request):
        categorias = Categoria.objects.filter(eliminado=False).all()
        dataSerializada = CategoriaSerializer(instance=categorias, many=True)
        return Response(data={
            "content": dataSerializada.data
        })

    def post(self, request: Request):
        serializador = CategoriaSerializer(data=request.data)
        if serializador.is_valid():
            serializador.save()
            return Response(data={
                "message": "Categoria creada exitosamente",
                "content": serializador.data,
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(data={
                "message": "Error al crear la categoria",
                "content": serializador.errors,
            }, status=status.HTTP_400_BAD_REQUEST)


class DevolverActualizarEliminarCategoriaView(RetrieveUpdateDestroyAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    lookup_field = "id"

    def retrieve(self, request, id):
        categoriaEncontrada = Categoria.objects.filter(eliminado=False, id=id).first()
        if not categoriaEncontrada:
            return Response(data={
                "message": "Categoria no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        dataSerializada = self.serializer_class(instance=categoriaEncontrada)
        return Response(data={
            "content": dataSerializada.data
        })

    def update(self, request, id):
        categoriaEncontrada = Categoria.objects.filter(eliminado=False, id=id).first()
        if not categoriaEncontrada:
            return Response(data={
                "message": "Categoria no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        serializador = self.serializer_class(data=request.data)
        if serializador.is_valid():
            serializador.update(categoriaEncontrada, serializador.validated_data)
            return Response(data={
                "message": "Categoria actualizada exitosamente",
                "content": serializador.data,
            })
        else:
            return Response(data={
                "message": "Error al actualizar la categoria",
                "content": serializador.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, id):
        categoriaEncontrada = Categoria.objects.filter(eliminado=False, id=id).first()
        if not categoriaEncontrada:
            return Response(data={
                "message": "Categoria no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        categoriaEncontrada.eliminado = True
        categoriaEncontrada.save()

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


class ProductosView(ViewSet):
    def create(self, request: Request):
        serializador = ProductoSerializer(data=request.data)
        categoriaEncontrada = Categoria.objects.filter(id=request.data.get("categoria"), eliminado=False).first()
        if not categoriaEncontrada:
            return Response({
                "message": "Error al crear el producto",
                "content": "Categoria no existe",
            }, status=status.HTTP_400_BAD_REQUEST)

        if serializador.is_valid():
            nuevoProducto = serializador.save()
            media = serializador.validated_data.get("media")
            if media:
                key = media.ruta + media.nombre + "." + media.ext
                s3 = client("s3")
                url = s3.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={
                        "Bucket": getenv("BUCKET_NAME"),
                        "Key": key,
                    },
                    ExpiresIn=30,
                )
                nuevoProducto.url = url
            return Response(data={
                "message": "Producto creado exitosamente",
                "content": serializador.data,
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(data={
                "message": "Error al crear el producto",
                "content": serializador.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request: Request):
        categoria = request.query_params.getlist("categoria")
        nombre = request.query_params.get("nombre")

        filtros = {
            "eliminado": False
        }

        if categoria:
            filtros["categoria__in"] = []
            for categoriaId in categoria:
                try:
                    UUID(categoriaId)
                except:
                    return Response(data={
                        "message": f"El id de la categoria {categoriaId} es invalido"
                    })

                categoriaEncontrada = Categoria.objects.filter(id=categoriaId, eliminado=False).first()
                if categoriaEncontrada:
                    filtros["categoria__in"].append(str(categoriaEncontrada.id))

            if len(filtros["categoria__in"]) == 0:
                del filtros["categoria__in"]

        if nombre:
            filtros["nombre__icontains"] = nombre.strip()

        productos = Producto.objects.filter(**filtros).all()

        paginador = PaginacionEstandar()
        resultado = paginador.paginate_queryset(productos, request, view=self)

        for producto in resultado:
            if producto.media:
                key = producto.media.ruta + producto.media.nombre + "." + producto.media.ext
                s3 = client("s3")
                url = s3.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={
                        "Bucket": getenv("BUCKET_NAME"),
                        "Key": key,
                    },
                    ExpiresIn=30,
                )
                producto.url = url

        serializador = ProductoSerializer(instance=resultado, many=True)
        respuesta = paginador.get_paginated_response(serializador.data)
        return respuesta


class ProductoView(ViewSet):
    def retrieve(self, request: Request, id):
        productoEncontrado = Producto.objects.filter(id=id, eliminado=False).first()

        if not productoEncontrado:
            return Response(data={
                "message": "Producto no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        serializador = ProductoDetalleSerializer(instance=productoEncontrado)
        return Response(data={
            "content": serializador.data
        })

    def destroy(self, request: Request, id):
        productoEncontrado = Producto.objects.filter(id=id, eliminado=False).first()

        if not productoEncontrado:
            return Response(data={
                "message": "Producto no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        productoEncontrado.eliminado = True
        productoEncontrado.save()

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


@api_view(http_method_names=["POST"])
def crearUrlParaSubirArchivo(request: Request):
    serializador = GenerarUrlAWSSerializer(data=request.data)
    if serializador.is_valid():
        fileName = serializador.validated_data.get("fileName")
        ext = serializador.validated_data.get("ext")
        contentType = serializador.validated_data.get("contentType")
        folder = serializador.validated_data.get("folder", "")

        s3 = client("s3")
        nombre = str(uuid4()) + "_" + fileName

        url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": getenv("BUCKET_NAME"),
                "Key": folder + nombre + "." + ext,
                "ContentType": contentType,
            },
            ExpiresIn=600,
        )

        return Response(data={
            "content": {
                "url": unquote(url),
                "nombre": nombre,
                "ext": ext,
                "mimeType": contentType,
                "ruta": folder,
            }
        })
    else:
        return Response(data={
            "message": "Error al generar la URL",
            "content": serializador.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(http_method_names=["POST"])
def crearMedia(request: Request):
    serializador = MediaSerializer(data=request.data)
    if serializador.is_valid():
        serializador.save()
        return Response(data={
            "message": "Archivo creado exitosamente",
            "content": {
                "id": serializador.data.get("id")
            },
        }, status=status.HTTP_201_CREATED)
    else:
        return Response(data={
            "message": "Error al crear el archivo",
            "content": serializador.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


class DespachosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        despachos = Despacho.objects.filter(eliminado=False).all()
        serializador = DespachoSerializer(instance=despachos, many=True)
        return Response(data={
            "content": serializador.data
        })

    def post(self, request: Request):
        usuarioExiste = Usuario.objects.filter(id=request.user.id).first()
        if not usuarioExiste:
            return Response(data={
                "message": "El usuario no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        productoEncontrado = Producto.objects.filter(id=request.data.get("producto"), eliminado=False).first()
        if not productoEncontrado:
            return Response(data={
                "message": "Producto no existe o fue eliminado"
            }, status=status.HTTP_400_BAD_REQUEST)

        request.data["usuario"] = usuarioExiste.id
        serializador = DespachoSerializer(data=request.data)

        if serializador.is_valid():
            cantidadSolicitada = serializador.validated_data.get("cantidadCajas")

            if cantidadSolicitada <= 0:
                return Response(data={
                    "message": "La cantidad de cajas debe ser mayor a cero"
                }, status=status.HTTP_400_BAD_REQUEST)

            if productoEncontrado.stock < cantidadSolicitada:
                return Response(data={
                    "message": f"Stock insuficiente. Actualmente solo hay {productoEncontrado.stock} cajas disponibles"
                }, status=status.HTTP_400_BAD_REQUEST)

            productoEncontrado.stock = productoEncontrado.stock - cantidadSolicitada
            productoEncontrado.save()

            serializador.save()

            return Response(data={
                "message": "Despacho registrado y stock descontado exitosamente",
                "content": serializador.data,
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(data={
                "message": "Error al registrar el despacho",
                "content": serializador.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
