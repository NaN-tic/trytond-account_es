"""Update company charts and assign general tax rules to eligible party fields.

Run after trytond-admin has updated the module. The retired templates have
been removed, so their company rules are identified by exact name.
Replace empty or selected tax rules, including those of inactive parties.
Delete the retired rules after updating all parties and company defaults.
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
retired_rule_names = [
    'Régimen Nacional',
    'Régimen Extracomunitario',
    'Régimen Extracomunitario territorios españoles excluidos del IVA',
    'Régimen Intracomunitario (Bienes)',
    'Régimen Intracomunitario (Servicios)',
    'Inversión del sujeto pasivo (Servicios)',
    'Inversión del sujeto pasivo (Bienes)',
    ]

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

rules_to_delete = []
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

        replaceable_rules = set(TaxRule.search([
                    ('company', '=', company.id),
                    ('name', 'in', retired_rule_names),
                    ]))
        rules_to_delete.extend(replaceable_rules)
        parties = Party.search([])
        for field, kind in [
                ('customer_tax_rule', 'sale'),
                ('supplier_tax_rule', 'purchase'),
                ]:
            updated = 0
            for batch in grouped_slice(parties, 1000):
                eligible = []
                for party in batch:
                    rule = getattr(party, field)
                    if not rule or rule in replaceable_rules:
                        eligible.append(party)
                if eligible:
                    Party.write(eligible, {field: rules[kind].id})
                    updated += len(eligible)
            print(f'{company.rec_name}: {field} updated for {updated} parties.')

        configuration = Configuration(1)
        configuration.default_customer_tax_rule = rules['sale']
        configuration.default_supplier_tax_rule = rules['purchase']
        configuration.save()
        print(f'{company.rec_name}: default tax rules updated.')

if rules_to_delete:
    TaxRule.delete(rules_to_delete)
    print(f'{len(rules_to_delete)} retired tax rules deleted.')

transaction.commit()
print('All changes committed.')
