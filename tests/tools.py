# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime

from dateutil.relativedelta import relativedelta

from proteus import Model, Wizard

from trytond.modules.company.tests.tools import get_company

__all__ = ['create_chart', 'get_account']


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

    account_template, = AccountTemplate.find([('id','=',data.db_id)])
    create_chart = Wizard('account.create_chart')
    create_chart.execute('account')

    create_chart.form.account_template = account_template
    create_chart.form.company = company
    create_chart.execute('create_account')

    create_chart.form.account_receivable = get_account('pgc_4300_child', company, config=config)
    create_chart.form.account_payable = get_account('pgc_4000_child', company, config=config)
    create_chart.execute('create_properties')
    return create_chart


def get_account(account_name, company=None, config=None):
    "Return spanish accounts per name"

    ModelData = Model.get('ir.model.data')
    Account = Model.get('account.account')

    data, = ModelData.find([
            ('module', '=', 'account_es'),
            ('fs_id','=',account_name),])
    if not company:
        company = get_company()
    account, = Account.find([('template', '=', data.db_id)])

    return account
