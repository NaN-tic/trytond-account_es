# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta

__all__ = ['Account', 'AccountTemplate', 'TypeTemplate']


class Account:
    __metaclass__ = PoolMeta
    __name__ = 'account.account'

    @classmethod
    def __setup__(cls):
        super(Account, cls).__setup__()
        value = ('efective', 'Efective')
        if value not in cls.kind.selection:
            cls.kind.selection.append(value)


class AccountTemplate:
    __metaclass__ = PoolMeta
    __name__ = 'account.account.template'

    @classmethod
    def check_xml_record(cls, records, values):
        return True


class TypeTemplate:
    __metaclass__ = PoolMeta
    __name__ = 'account.account.type.template'

    @classmethod
    def check_xml_record(cls, records, values):
        return True
