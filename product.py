from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval


class Category(metaclass=PoolMeta):
    __name__ = 'product.category'

    @classmethod
    def __setup__(cls):
        pool = Pool()
        AccountType = pool.get('account.account.type')

        super().__setup__()

        # Related to module account_product
        if hasattr(cls, 'account_expense'):
            if hasattr(AccountType, 'fixed_asset'):
                cls.account_expense.domain = [
                    ('company', '=', Eval('context', {}).get('company', -1)),
                    ['OR',
                        [
                            ('type.supplier_balance', '=', True),
                            ('type.fixed_asset', '=', False),
                            ],
                        ('type.expense', '=', True),
                        ],
                    ]
            else:
                cls.account_expense.domain = [
                    ('company', '=', Eval('context', {}).get('company', -1)),
                    ['OR',
                        ('type.expense', '=', True),
                        ('type.supplier_balance', '=', True),
                        ],
                    ]


class CategoryAccount(metaclass=PoolMeta):
    __name__ = 'product.category.account'

    @classmethod
    def __setup__(cls):
        pool = Pool()
        AccountType = pool.get('account.account.type')

        super().__setup__()

        # Related to module account_product
        if hasattr(cls, 'account_expense'):
            if hasattr(AccountType, 'fixed_asset'):
                cls.account_expense.domain = [
                    ('company', '=', Eval('company', -1)),
                    ['OR',
                        [
                            ('type.supplier_balance', '=', True),
                            ('type.fixed_asset', '=', False),
                            ],
                        ('type.expense', '=', True),
                        ],
                    ]
            else:
                cls.account_expense.domain = [
                    ('company', '=', Eval('company', -1)),
                    ['OR',
                        ('type.expense', '=', True),
                        ('type.supplier_balance', '=', True),
                        ],
                    ]


class AccountTypeMixin:
    __slots__ = ()

    @classmethod
    def _account_es_company_domain(cls):
        return ('company', '=', Eval('context', {}).get('company', -1))

    @classmethod
    def __setup__(cls):
        pool = Pool()
        AccountType = pool.get('account.account.type')

        super().__setup__()

        # Related to module account_product_accounting
        if hasattr(cls, 'account_expense'):
            if hasattr(AccountType, 'fixed_asset'):
                cls.account_expense.domain = [
                    cls._account_es_company_domain(),
                    ['OR',
                        [
                            ('type.supplier_balance', '=', True),
                            ('type.fixed_asset', '=', False),
                            ],
                        ('type.expense', '=', True),
                        ],
                    ]
            else:
                cls.account_expense.domain = [
                    cls._account_es_company_domain(),
                    ['OR',
                        ('type.expense', '=', True),
                        ('type.supplier_balance', '=', True),
                        ],
                    ]


class Template(AccountTypeMixin, metaclass=PoolMeta):
    __name__ = 'product.template'


class TemplateAccount(AccountTypeMixin, metaclass=PoolMeta):
    __name__ = 'product.template.account'

    @classmethod
    def _account_es_company_domain(cls):
        return ('company', '=', Eval('company', -1))
