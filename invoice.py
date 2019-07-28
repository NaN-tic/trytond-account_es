from trytond.pool import PoolMeta

__all__ = ['InvoiceLine']


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

