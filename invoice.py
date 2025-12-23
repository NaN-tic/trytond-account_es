# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.model import fields
from trytond.transaction import Transaction


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

    def _compute_taxes(self):
        ppol = Pool()
        Currency = ppol.get('currency.currency')
        TaxLine = ppol.get('account.tax.line')

        tax_lines = super()._compute_taxes()
        context = Transaction().context
        if (getattr(self, 'invoice', None)
                and getattr(self.invoice, 'type', None)):
            invoice_type = self.invoice.type
        else:
            invoice_type = getattr(self, 'invoice_type', None)
        if invoice_type == 'in':
            if context.get('_deductible_rate') is not None:
                deductible_rate = context['_deductible_rate']
            else:
                deductible_rate = getattr(self, 'taxes_deductible_rate', 1)
            if deductible_rate is not None and deductible_rate != 1:
                with Transaction().set_context(_deductible_rate=1):
                    taxes = self._get_taxes().values()
                for tax in taxes:
                    base = tax['base'] * (1 - deductible_rate)
                    with Transaction().set_context(
                            date=self.invoice.currency_date):
                        base = Currency.compute(
                            self.invoice.currency, base,
                            self.invoice.company.currency)
                    tax_line = TaxLine()
                    tax_line.amount = base
                    tax_line.type = 'base'
                    tax_line.tax = tax['tax']
                    tax_lines.append(tax_line)
        return tax_lines
