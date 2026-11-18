"""Update company charts and assign the general tax rules to all parties.

Existing party tax rules are overwritten, including those of inactive parties.
All changes are committed together after every company has been processed.
"""

from trytond.tools import grouped_slice


pool = globals()['pool']
transaction = globals()['transaction']


Company = pool.get('company.company')
Account = pool.get('account.account')
Party = pool.get('party.party')
Configuration = pool.get('account.configuration')
TaxRule = pool.get('account.tax.rule')
ModelData = pool.get('ir.model.data')
UpdateChart = pool.get('account.update_chart', type='wizard')

sale_template = ModelData.get_id('account_es', 'fp_general_sale')
purchase_template = ModelData.get_id('account_es', 'fp_general_purchase')

with transaction.set_context(active_test=False):
    companies = Company.search([])

# Update every chart before assigning the resulting company tax rules.
for company in companies:
    with transaction.set_context(company=company.id, active_test=False):
        roots = Account.search([
                ('company', '=', company.id),
                ('parent', '=', None),
                ('template', '!=', None),
                ])
        if len(roots) != 1:
            raise ValueError(
                f'{company.rec_name}: expected one chart root with a '
                f'template, found {len(roots)}.')

        session_id, _, _ = UpdateChart.create()
        UpdateChart.execute(session_id, {
                'start': {'account': roots[0].id},
                }, 'update')
        UpdateChart.delete(session_id)
        print(f'{company.rec_name}: chart updated.')

for company in companies:
    with transaction.set_context(company=company.id, active_test=False):
        rules = {}
        for kind, template in [
                ('sale', sale_template),
                ('purchase', purchase_template),
                ]:
            matches = TaxRule.search([
                    ('company', '=', company.id),
                    ('template', '=', template),
                    ('kind', 'in', [kind, 'both']),
                    ])
            if len(matches) != 1:
                raise ValueError(
                    f'{company.rec_name}: expected one general {kind} '
                    f'tax rule, found {len(matches)}.')
            rules[kind] = matches[0]

        parties = Party.search([])
        for batch in grouped_slice(parties, 1000):
            Party.write(list(batch), {
                    'customer_tax_rule': rules['sale'].id,
                    'supplier_tax_rule': rules['purchase'].id,
                    })

        configuration = Configuration(1)
        configuration.default_customer_tax_rule = rules['sale']
        configuration.default_supplier_tax_rule = rules['purchase']
        configuration.save()
        print(f'{company.rec_name}: {len(parties)} parties and '
            'default tax rules updated.')

transaction.commit()
print('All changes committed.')
