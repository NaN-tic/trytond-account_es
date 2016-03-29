# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['TaxTemplate', 'Tax', 'Account']


class TaxTemplate:
    __metaclass__ = PoolMeta
    __name__ = 'account.tax.template'

    report_description = fields.Text('Report Description', translate=True)
    recargo_equivalencia = fields.Boolean('Recargo Equivalencia',
        help='Indicates if the tax is Recargo de Equivalencia')

    def _get_tax_value(self, tax=None):
        res = super(TaxTemplate, self)._get_tax_value(tax)

        if not tax or tax.report_description != self.report_description:
            res['report_description'] = self.report_description
        if not tax or tax.recargo_equivalencia != self.recargo_equivalencia:
            res['recargo_equivalencia'] = self.recargo_equivalencia
        return res


class Tax():
    __metaclass__ = PoolMeta
    __name__ = 'account.tax'

    report_description = fields.Text('Report Description', translate=True)
    recargo_equivalencia = fields.Boolean('Recargo Equivalencia',
        help='Indicates if the tax is Recargo de Equivalencia')


class Account():
    __metaclass__ = PoolMeta
    __name__ = 'account.account'

    @classmethod
    def __setup__(cls):
        super(Account, cls).__setup__()
        value = ('efective', 'Efective')
        if value not in cls.kind.selection:
            cls.kind.selection.append(value)
