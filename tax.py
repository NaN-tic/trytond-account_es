# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['TaxCodeTemplate', 'TaxRuleTemplate', 'TaxRuleLineTemplate',
    'TaxTemplate', 'Tax']


class TaxCodeTemplate:
    __metaclass__ = PoolMeta
    __name__ = 'account.tax.code.template'

    @classmethod
    def check_xml_record(cls, records, values):
        return True


class TaxRuleTemplate:
    __metaclass__ = PoolMeta
    __name__ = 'account.tax.rule.template'

    @classmethod
    def check_xml_record(cls, records, values):
        return True


class TaxRuleLineTemplate:
    __metaclass__ = PoolMeta
    __name__ = 'account.tax.rule.line.template'

    @classmethod
    def check_xml_record(cls, records, values):
        return True


class TaxTemplate:
    __metaclass__ = PoolMeta
    __name__ = 'account.tax.template'

    report_description = fields.Text('Report Description', translate=True)
    recargo_equivalencia = fields.Boolean('Recargo Equivalencia',
        help='Indicates if the tax is Recargo de Equivalencia')
    deducible = fields.Boolean('Deducible',
        help='Indicates if the tax is deductible')

    def _get_tax_value(self, tax=None):
        res = super(TaxTemplate, self)._get_tax_value(tax)

        if not tax or tax.report_description != self.report_description:
            res['report_description'] = self.report_description
        if not tax or tax.recargo_equivalencia != self.recargo_equivalencia:
            res['recargo_equivalencia'] = self.recargo_equivalencia
        if not tax or tax.deducible != self.deducible:
            res['deducible'] = self.deducible
        return res

    @classmethod
    def check_xml_record(cls, records, values):
        return True


class Tax:
    __metaclass__ = PoolMeta
    __name__ = 'account.tax'

    report_description = fields.Text('Report Description', translate=True)
    recargo_equivalencia = fields.Boolean('Recargo Equivalencia',
        help='Indicates if the tax is Recargo de Equivalencia')
    deducible = fields.Boolean('Deducible',
        help='Indicates if the tax is deductible')

    @staticmethod
    def default_deducible():
        return True
