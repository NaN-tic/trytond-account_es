# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import If, Eval, Bool

__all__ = ['Account', 'AccountTemplate', 'FiscalYear', 'Period',
    'AccountTypeTemplate', 'AccountType']


class Account(metaclass=PoolMeta):
    __name__ = 'account.account'

    # TODO
    # @classmethod
    # def __setup__(cls):
    #     super(Account, cls).__setup__()
    #     value = ('efective', 'Efective')
    #     if value not in cls.type.selection:
    #         cls.type.selection.append(value)


class AccountTemplate(metaclass=PoolMeta):
    __name__ = 'account.account.template'

    @classmethod
    def check_xml_record(cls, records, values):
        return True


class FiscalYear(metaclass=PoolMeta):
    __name__ = 'account.fiscalyear'
    code = fields.Char('Code', size=None)

    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
            ('code',) + tuple(clause[1:]),
            (cls._rec_name,) + tuple(clause[1:]),
            ]


class Period(metaclass=PoolMeta):
    __name__ = 'account.period'
    code = fields.Char('Code', size=None)

    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
            ('code',) + tuple(clause[1:]),
            (cls._rec_name,) + tuple(clause[1:]),
            ]


def AccountTypeMixin(template=False):

    class Mixin:
        supplier_balance = fields.Boolean(
            "Supplier Balance", domain=[
                If(Eval('statement') != 'balance',
                    ('supplier_balance', '=', False), ()),
                ],
            states={
                'invisible': Eval('statement') != 'balance',
                },
            depends=['statement'], help='Check to be able to use this balance '
            'account in supplier invoice lines.')
        customer_balance = fields.Boolean(
            "Customer Balance", domain=[
                If(Eval('statement') != 'balance',
                    ('customer_balance', '=', False), ()),
                ],
            states={
                'invisible': Eval('statement') != 'balance',
                },
            depends=['statement'], help='Check to be able to use this balance '
            'account in customer invoice lines.')
    if not template:
        for fname in dir(Mixin):
            field = getattr(Mixin, fname)
            if not isinstance(field, fields.Field):
                continue
            field.states['readonly'] = (
                Bool(Eval('template', -1)) & ~Eval('template_override', False))
    return Mixin


class AccountTypeTemplate(AccountTypeMixin(template=True), metaclass=PoolMeta):
    __name__ = 'account.account.type.template'

    def _get_type_value(self, type=None):
        values = super()._get_type_value(type=type)
        if not type or type.supplier_balance != self.supplier_balance:
            values['supplier_balance'] = self.supplier_balance
        if not type or type.customer_balance != self.customer_balance:
            values['customer_balance'] = self.customer_balance
        return values

    @classmethod
    def check_xml_record(cls, records, values):
        return True


class AccountType(AccountTypeMixin(), metaclass=PoolMeta):
    __name__ = 'account.account.type'
