#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Tax', 'Account']

__metaclass__ = PoolMeta


class Tax():
    __name__ = 'account.tax'

    recargo_equivalencia = fields.Boolean('Recargo Equivalencia',
        help='Indicates if the tax is Recargo de Equivalencia')


class Account():
    __name__ = 'account.account'

    @classmethod
    def __setup__(cls):
        super(Account, cls).__setup__()
        value = ('efective', 'Efective')
        if not value in cls.kind.selection:
            cls.kind.selection.append(value)
