from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status
from rest_framework.compat import set_rollback
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _
from django.utils import six
import logging

from shop.api import errors

logger = logging.getLogger('docs.view')


class ForeignObjectRelDeleteError(Exception):
    pass


class ModelDontHaveIsActiveFiled(Exception):
    pass


class RestPermissionDenied(Exception):
    pass


class Error(Exception):

    def __init__(self, err_code, err_message='Internal Server Error',
                 message=u'服务器异常', status_code=status.HTTP_400_BAD_REQUEST):
        self.err_code = err_code
        self.err_message = err_message
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return u'[Error] %d: %s(%d)' % (self.err_code,
                                        self.err_message, self.status_code)

    def getResponse(self):
        return ErrorResponse(self.err_code,
                             self.err_message, self.message, self.status_code)


def ErrorResponse(err_code=errors.SYSTEM_ERROR,
                  err_message='Internal Server Error',
                  message=u'服务器异常',
                  status=status.HTTP_400_BAD_REQUEST, headers=None):
    err = {
        'success': False,
        'error_code': err_code,
        'error': err_message,
        'message': message,
    }
    return Response(err, status, headers=headers)


def custom_exception_handler(exc, context):

    if isinstance(exc, Error):
        set_rollback()
        return ErrorResponse(exc.err_code, exc.err_message,
                             exc.message, status=exc.status_code)

    if isinstance(exc, (ForeignObjectRelDeleteError,
                        ModelDontHaveIsActiveFiled)):
        set_rollback()
        return ErrorResponse(errors.PermissionDenied, str(exc),
                             u'抱歉, 已有其他数据与之关联, 禁止删除',
                             status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, (RestPermissionDenied, PermissionDenied)):
        msg = _('Permission denied.')
        data = {
            'detail': six.text_type(msg)
        }
        exc_message = str(exc)
        if 'CSRF' in exc_message:
            data['detail'] = exc_message

        set_rollback()
        return ErrorResponse(errors.PermissionDenied, data,
                             u'opps, 没有对应的权限',
                             status=status.HTTP_403_FORBIDDEN)

    # Note: Unhandled exceptions will raise a 500 error.
    # return ErrorResponse(errors.SYSTEM_ERROR, 'Internal Server Error',
    # status.HTTP_500_INTERNAL_SERVER_ERROR)
