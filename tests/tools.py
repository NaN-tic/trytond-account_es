# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from proteus import Model, Wizard
from trytond.modules.company.tests.tools import get_company

__all__ = ['create_chart']


def create_chart(company=None, config=None):
    "Create chart of accounts"
    AccountTemplate = Model.get('account.account.template', config=config)
    ModelData = Model.get('ir.model.data')

    if not company:
        company = get_company()
    data, = ModelData.find([
            ('module', '=', 'account_es'),
            ('fs_id', '=', 'pgc_0'),
            ], limit=1)

    account_template = AccountTemplate(data.db_id)

    create_chart = Wizard('account.create_chart')
    create_chart.execute('account')
    create_chart.form.account_template = account_template
    create_chart.form.company = company
    create_chart.execute('create_account')

    accounts = get_accounts(company, config=config)

    create_chart.form.account_receivable = accounts['receivable']
    create_chart.form.account_payable = accounts['payable']
    create_chart.execute('create_properties')
    return create_chart


def get_accounts(company=None, config=None):
    "Return accounts per kind"
    Account = Model.get('account.account', config=config)
    Data  = Model.get('ir.model.data', config=config)

    pgc_570, = Data.find([
            ('module', '=', 'account_es'),
            ('fs_id', '=', 'pgc_570_child')], limit=1)
    if not company:
        company = get_company()
    accounts = {}
    accounts['receivable'], = Account.find([
            ('type.receivable', '=', True),
            ('company', '=', company.id),
            ], limit=1)
    accounts['payable'], = Account.find([
            ('type.payable', '=', True),
            ('company', '=', company.id),
            ], limit=1)
    accounts['revenue'], = Account.find([
            ('type.revenue', '=', True),
            ('company', '=', company.id),
            ], limit=1)
    accounts['expense'], = Account.find([
            ('type.expense', '=', True),
            ('company', '=', company.id),
            ], limit=1)
    accounts['cash'], = Account.find([
            ('company', '=', company.id),
            ('template', '=', pgc_570.db_id),
            ], limit=1)
    return accounts

def get_taxes(company=None, config=None):
    "Return accounts per kind"
    Account = Model.get('account.tax', config=config)
    Data  = Model.get('ir.model.data', config=config)

    iva_rep_21, = Data.find([
            ('module', '=', 'account_es'),
            ('fs_id', '=', 'iva_rep_21')], limit=1)
    iva_X21_compras_bc, = Data.find([
            ('module', '=', 'account_es'),
            ('fs_id', '=', 'iva_X21_compras_bc')], limit=1)
    if not company:
        company = get_company()
    taxes = {}
    taxes['customer_tax'], = Account.find([
            ('template', '=', iva_rep_21.db_id),
            ('company', '=', company.id),
            ], limit=1)
    taxes['supplier_tax'], = Account.find([
            ('template', '=', iva_X21_compras_bc.db_id),
            ('company', '=', company.id),
            ], limit=1)
    return taxes
