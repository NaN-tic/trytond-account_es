# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal
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
        Tax = ppol.get('account.tax')

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
                for tax_vals in taxes:
                    tax = Tax(tax_vals.tax)
                    if tax.tax_kind != 'vat':
                        continue
                    base = tax_vals.base * deductible_rate
                    with Transaction().set_context(
                            date=self.invoice.currency_date):
                        base = Currency.compute(
                            self.invoice.currency, base,
                            self.invoice.company.currency)
                    tax_line = TaxLine()
                    tax_line.amount = base
                    tax_line.type = 'base'
                    tax_line.tax = tax_vals.tax
                    tax_lines.append(tax_line)
        return tax_lines

    @property
    def taxable_lines(self):
        taxable_lines = super().taxable_lines
        context = Transaction().context
        if (getattr(self, 'invoice', None)
                and getattr(self.invoice, 'type', None)):
            invoice_type = self.invoice.type
        else:
            invoice_type = getattr(self, 'invoice_type', None)
        if context.get('_deductible_rate') is not None:
            deductible_rate = context['_deductible_rate']
        else:
            deductible_rate = getattr(self, 'taxes_deductible_rate', 1)
        if not (invoice_type == 'in' and deductible_rate is not None
                and deductible_rate != 1):
            return taxable_lines

        taxes = getattr(self, 'taxes', []) or []
        unit_price = getattr(self, 'unit_price', None) or Decimal(0)
        quantity = getattr(self, 'quantity', None) or 0
        tax_date = getattr(self, 'tax_date', None)
        non_vat_taxes = [t for t in taxes if t.tax_kind != 'vat']
        vat_taxes = [t for t in taxes if t.tax_kind == 'vat']

        result = [
            (non_vat_taxes, unit_price, quantity, tax_date),
        ]
        if deductible_rate != 0:
            result.append((
                    vat_taxes,
                    unit_price * (1 - deductible_rate),
                    quantity,
                    tax_date,
                    ))
        return result

    @fields.depends(
        'type', 'quantity', 'unit_price', 'taxes_deductible_rate', 'invoice',
        '_parent_invoice.currency', 'currency', 'taxes',
        '_parent_invoice.type', 'invoice_type',
        methods=['_get_taxes'])
    def on_change_with_amount(self):
        pool = Pool()
        Tax = pool.get('account.tax')

        if self.type == 'line':
            invoice_type = (
                self.invoice.type if self.invoice else self.invoice_type)
            if (invoice_type == 'in'
                    and self.taxes_deductible_rate is not None
                    and self.taxes_deductible_rate != 1):
                currency = (self.invoice.currency if self.invoice
                    else self.currency)
                amount = (Decimal(str(self.quantity or 0))
                    * (self.unit_price or Decimal(0)))
                with Transaction().set_context(_deductible_rate=1):
                    for tax_vals in self._get_taxes().values():
                        tax = Tax(tax_vals.tax)
                        taxes_deductible_rate = (self.taxes_deductible_rate
                            if tax.tax_kind == 'vat' else 1)
                        amount += tax_vals.amount * (
                            1 - taxes_deductible_rate)
                if currency:
                    return currency.round(amount)
                return amount
        return super().on_change_with_amount()
