#
#
# class Constants(object):
#     """
#     Create objects with read-only (constant) attributes.
#     Example:
#         Nums = Constants(ONE=1, PI=3.14159, DefaultWidth=100.0)
#         print 10 + Nums.PI
#         print '----- Following line is deliberate ValueError -----'
#         Nums.PI = 22
#     """
#
#     def __init__(self, *args, **kwargs):
#         self._d = dict(*args, **kwargs)
#
#     def __iter__(self):
#         return iter(self._d)
#
#     def __len__(self):
#         return len(self._d)
#
#     # NOTE: This is only called if self lacks the attribute.
#     # So it does not interfere with get of 'self._d', etc.
#     def __getattr__(self, name):
#         return self._d[name]
#
#     # ASSUMES '_..' attribute is OK to set. Need this to initialize 'self._d', etc.
#     # If use as keys, they won't be constant.
#     def __setattr__(self, name, value):
#         if (name[0] == '_'):
#             super(Constants, self).__setattr__(name, value)
#         else:
#             raise ValueError("setattr while locked", self)
#
#
# errors = Constants(SYSTEM_ERROR=500, PermissionDenied=501)
#
#
#
# # if (__name__ == "__main__"):
# #     # Usage example.
# #     Nums = Constants(ONE=1, PI=3.14159, DefaultWidth=100.0)
# #     print(10 + Nums.PI)
# #     print('----- Following line is deliberate ValueError -----')
# #     Nums.PI = 22


SYSTEM_ERROR = 500

BAD_PARAMS = 400

PermissionDenied = 501

NOT_PAY = 2001

NOT_LOGIN = 401

NOT_FOUND = 404

IS_USE = 1001

STOCK_IS_EMPTY = 1002

PAY_ERROR = 1003
