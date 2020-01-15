from trytond.pool import PoolMeta

__all__ = ['Invoice', 'InvoiceLine']


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    def _get_move_line(self, date, amount):
        line = super(Invoice, self)._get_move_line(date, amount)
        if line.description:
            if self.party.name not in line.description:
                line.description = self.party.name + ' ' + line.description
            if self.number not in line.description:
                line.description = self.number + ' ' + line.description
        else:
            line.description = self.number + ' ' + self.party.name
        return line


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

