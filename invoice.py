# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import fields


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    aeat_qr_url = fields.Function(fields.Char('AEAT QR URL'),
            'get_aeat_qr_url')
    simplified = fields.Function(fields.Boolean('Is Simplified Invoice'),
            'get_simplified')

    def get_simplified(self, name):
        if self.type == 'in':
            return False
        if self.party_tax_identifier:
            return False
        if getattr(self.party, 'vat_required', False):
            return False
        return True

    def get_aeat_qr_url(self, name):
        return


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    @classmethod
    def _account_domain(cls, type_):
        domain = super()._account_domain(type_)
        if type_ == 'out':
            domain.append(('type.customer_balance', '=', True))
        elif type_ == 'in':
            domain.append(('type.supplier_balance', '=', True))
        return domain
