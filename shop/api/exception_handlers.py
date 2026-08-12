from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler

from shop.core.exceptions import ApplicationError


def application_exception_handler(exc, ctx) -> Response | None:
    """
    Normalize every error into `{"message": ..., "extra": {...}}`.

    Based on the handler proposed by the HackSoft Django Styleguide:
    https://github.com/HackSoftware/Django-Styleguide#approach-2---hacksofts-proposed-way
    """
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(as_serializer_error(exc))

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()

    if isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = exception_handler(exc, ctx)

    # DRF does not handle `ApplicationError` (and anything else that is not an
    # `APIException`), so `response` is `None` at this point.
    if response is None:
        if isinstance(exc, ApplicationError):
            return Response({"message": exc.message, "extra": exc.extra}, status=400)

        return response

    if isinstance(exc.detail, (list, dict)):
        response.data = {"detail": response.data}

    if isinstance(exc, exceptions.ValidationError):
        response.data["message"] = "Ошибка валидации"
        response.data["extra"] = {"fields": response.data.pop("detail")}
    else:
        response.data["message"] = response.data.pop("detail", str(exc))
        response.data["extra"] = {}

    return response
