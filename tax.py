# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval

__all__ = ['TaxCodeTemplate', 'TaxRuleTemplate', 'TaxRuleLineTemplate',
    'TaxTemplate', 'Tax']


class TaxCodeTemplate(metaclass=PoolMeta):
    __name__ = 'account.tax.code.template'

    @classmethod
    def check_xml_record(cls, records, values):
        return True


class TaxRuleTemplate(metaclass=PoolMeta):
    __name__ = 'account.tax.rule.template'

    @classmethod
    def check_xml_record(cls, records, values):
        return True


class TaxRuleLineTemplate(metaclass=PoolMeta):
    __name__ = 'account.tax.rule.line.template'

    @classmethod
    def check_xml_record(cls, records, values):
        return True


class TaxTemplate(metaclass=PoolMeta):
    __name__ = 'account.tax.template'

    report_description = fields.Text('Report Description', translate=True)
    recargo_equivalencia = fields.Boolean('Recargo Equivalencia',
        help='Indicates if the tax is Recargo de Equivalencia')
    recargo_equivalencia_related_tax = fields.Many2One(
        'account.tax.template', 'Recargo Equivalencia Related Tax',
        domain=[
            ('recargo_equivalencia', '=', True),
            ], depends=['recargo_equivalencia'],
        help='The possible Recargo Equivalencia related to this tax')
    deducible = fields.Boolean('Deducible',
        help='Indicates if the tax is deductible')
    code_lines = fields.One2Many('account.tax.code.line.template', 'tax',
        'Code Lines')

    @classmethod
    def __setup__(cls):
        super(TaxTemplate, cls).__setup__()
        cls.invoice_account.domain.remove(('type.statement','=', 'balance'))
        cls.credit_note_account.domain.remove(('type.statement','=', 'balance'))

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
    def update_recargo_equivalencia_related_tax(cls, template2tax):
        templates = cls.search([('recargo_equivalencia_related_tax',
            '!=', None)])
        Tax = Pool().get('account.tax')
        for template in templates:
            tax = Tax(template2tax[template.id])
            tax.recargo_equivalencia_related_tax = template2tax[
                template.recargo_equivalencia_related_tax.id]
            tax.save()


    @classmethod
    def update_tax(cls, company_id, template2account, template2tax=None):
        super(TaxTemplate, cls).update_tax(account_id, company_id,
            template2account, template2tax)
        cls.update_recargo_equivalencia_related_tax(template2tax)

    @classmethod
    def create_tax(cls, account_id, company_id, template2account,
            template2tax):
        super(TaxTemplate, cls).create_tax(account_id, company_id,
            template2account, template2tax)
        cls.update_recargo_equivalencia_related_tax(template2tax)




    @classmethod
    def check_xml_record(cls, records, values):
        return True


class Tax(metaclass=PoolMeta):
    __name__ = 'account.tax'

    report_description = fields.Text('Report Description', translate=True)
    recargo_equivalencia = fields.Boolean('Recargo Equivalencia',
        help='Indicates if the tax is Recargo de Equivalencia')
    recargo_equivalencia_related_tax = fields.Many2One(
        'account.tax', 'Recargo Equivalencia Related Tax',
        domain=[
            ('recargo_equivalencia', '=', True),
            ('company', '=', Eval('company', -1)),
            ], depends=['recargo_equivalencia', 'company'],
        help='The possible Recargo Equivalencia related to this tax')
    deducible = fields.Boolean('Deducible',
        help='Indicates if the tax is deductible')
    code_lines = fields.One2Many('account.tax.code.line', 'tax',
        'Code Lines')

    @classmethod
    def __setup__(cls):
        super(Tax, cls).__setup__()
        cls.invoice_account.domain.remove(('type.statement','=', 'balance'))
        cls.credit_note_account.domain.remove(('type.statement','=', 'balance'))

    @staticmethod
    def default_deducible():
        return True
