# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['Invoice', 'InvoiceLine']


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    def _get_move_line(self, date, amount):
        line = super(Invoice, self)._get_move_line(date, amount)
        number = self.reference or self.number if self.type == 'in' else self.number
        if line.description:
            if self.party.name not in line.description:
                line.description = self.party.name + ' ' + line.description
            if number not in line.description:
                line.description = number + ' ' + line.description
        else:
            line.description = number + ' ' + self.party.name
        return line

    @classmethod
    def cancel(cls, invoices):
        for invoice in invoices:
            if not invoice.move:
                continue
            if invoice.move.state != 'posted':
                raise UserError(gettext(
                    'account_es.msg_cancel_invoice_with_move_post'))

        return super(Invoice, cls).cancel(invoices)


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
