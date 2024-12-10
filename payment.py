# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta


class AccountPaymentClearing(metaclass=PoolMeta):
    __name__ = 'account.payment'

    @classmethod
    def _account_type_domain(cls):
        # not call super()
        # not add domain in case account.type is receivable or payable
        return ()
