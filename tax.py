# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval


class TaxCodeTemplate(metaclass=PoolMeta):
    __name__ = 'account.tax.code.template'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(0, ('name', 'ASC'))

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

    report_description = fields.Text('Report Description')
    tax_kind = fields.Selection([
        (None, ''),
        ('vat', 'VAT'),
        ('irpf', 'IRPF'),
        ('surcharge', 'Equivalence Surcharge'),
        ('reimbursements', 'Reimbursements'),
        ], 'Tax Kind')
    recargo_equivalencia_related_tax = fields.Many2One(
        'account.tax.template', 'Recargo Equivalencia Related Tax',
        domain=[
            ('tax_kind', '=', 'surcharge'),
            ],
        help='The possible Recargo Equivalencia related to this tax')
    deducible = fields.Boolean('Deducible',
        help='Indicates if the tax is deductible')
    code_lines = fields.One2Many('account.tax.code.line.template', 'tax',
        'Code Lines')
    isp = fields.Boolean('Inversion del Sujeto Pasivo',
        help='Indicates if the tax is Inversion del sujeto Pasivo')
    service = fields.Boolean('Service Rate',
        help='Indicates if the tax is used for services')

    @classmethod
    def __setup__(cls):
        super(TaxTemplate, cls).__setup__()
        cls.invoice_account.domain.remove(('type.statement', '=', 'balance'))
        cls.credit_note_account.domain.remove(
            ('type.statement', '=', 'balance'))

    @classmethod
    def __register__(cls, module_name):
        table_h = cls.__table_handler__(module_name)

        surcharge_exist = table_h.column_exist('recargo_equivalencia')
        super().__register__(module_name)
        if surcharge_exist:
            table_h.drop_column('recargo_equivalencia')

    def _get_tax_value(self, tax=None):
        res = super(TaxTemplate, self)._get_tax_value(tax)

        if not tax or tax.report_description != self.report_description:
            res['report_description'] = self.report_description
        if not tax or tax.tax_kind != self.tax_kind:
            res['tax_kind'] = self.tax_kind
        if not tax or tax.deducible != self.deducible:
            res['deducible'] = self.deducible
        if not tax or tax.isp != self.isp:
            res['isp'] = self.isp
        if not tax or tax.service != self.service:
            res['service'] = self.service
        return res

    def defult_tax_type(self):
        return 'vat'

    @staticmethod
    def default_tax_kind():
        return None

    @classmethod
    def update_recargo_equivalencia_related_tax(cls, template2tax):
        pool = Pool()
        Tax = pool.get('account.tax')

        templates = cls.search([
            ('recargo_equivalencia_related_tax', '!=', None),
            ])
        for template in templates:
            if template2tax.get(template.id):
                tax = Tax(template2tax[template.id])
                tax.recargo_equivalencia_related_tax = template2tax[
                    template.recargo_equivalencia_related_tax.id]
                tax.save()

    @classmethod
    def update_tax(cls, company_id, template2account, template2tax=None):
        super(TaxTemplate, cls).update_tax(company_id,
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

    @fields.depends('childs', 'isp')
    def on_change_isp(self):
        for child in self.childs:
            child.isp = self.isp

    @fields.depends('childs', 'service')
    def on_change_service(self):
        for child in self.childs:
            child.service = self.service


class Tax(metaclass=PoolMeta):
    __name__ = 'account.tax'

    report_description = fields.Text('Report Description', translate=True)
    tax_kind = fields.Selection([
        (None, ''),
        ('vat', 'VAT'),
        ('irpf', 'IRPF'),
        ('surcharge', 'Equivalence Surcharge'),
        ('reimbursements', 'Reimbursements'),
        ], 'Tax Kind')
    recargo_equivalencia_related_tax = fields.Many2One(
        'account.tax', 'Recargo Equivalencia Related Tax',
        domain=[
            ('tax_kind', '=', 'surcharge'),
            ('company', '=', Eval('company', -1)),
            ],
        help='The possible Recargo Equivalencia related to this tax')
    deducible = fields.Boolean('Deducible',
        help='Indicates if the tax is deductible')
    code_lines = fields.One2Many('account.tax.code.line', 'tax',
        'Code Lines')
    isp = fields.Boolean('Inversion del Sujeto Pasivo',
        help='Indicates if the tax is Inversion del sujeto Pasivo')
    service = fields.Boolean('Service Rate',
        help='Indicates if the tax is used for services')

    @classmethod
    def __register__(cls, module_name):
        table_h = cls.__table_handler__(module_name)

        surcharge_exist = table_h.column_exist('recargo_equivalencia')
        super().__register__(module_name)
        if surcharge_exist:
            table_h.drop_column('recargo_equivalencia')

    @classmethod
    def __setup__(cls):
        super(Tax, cls).__setup__()
        cls.invoice_account.domain.remove(('type.statement', '=', 'balance'))
        cls.credit_note_account.domain.remove(
            ('type.statement', '=', 'balance'))

    @staticmethod
    def default_tax_kind():
        return None

    @staticmethod
    def default_deducible():
        return True

    @fields.depends('childs', 'isp')
    def on_change_isp(self):
        for child in self.childs:
            child.isp = self.isp

    @fields.depends('childs', 'service')
    def on_change_service(self):
        for child in self.childs:
            child.service = self.service


class TaxCode(metaclass=PoolMeta):
    __name__ = 'account.tax.code'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(0, ('name', 'ASC'))
