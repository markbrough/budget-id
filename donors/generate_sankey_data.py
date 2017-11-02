# 1. Add up total amounts from each donor to each category
# 2. Add up total amounts from each category to each vote

from lxml import etree
import unicodecsv
import json

CSVfilename = 'donors-data.csv'

def getOrgCode(org_name, org_codes):
    if org_name in org_codes['known']:
        return org_codes['known'][org_name]
    org_codes['known'][org_name] = org_codes['num_known']
    org_codes['num_known'] = org_codes['num_known']+1
    return org_codes['known'][org_name]

def getTotalCosts(filename):
    donor_category = {}
    category_vote = {}
    orgcodes = {'known': {},
                'num_known': 0}
    
    donorsdata_file = open(filename)
    donorsdata_rows = unicodecsv.DictReader(donorsdata_file)
    for row in donorsdata_rows:
        if row['spine_category_code'] == "":
            row['spine_category_code'] = "unknown-spine"
            row['spine_category'] = "Unknown spine category"

        if row['vote_code'] == "":
            row['vote_code'] = "unknown-vote"
            row['vote_name'] = "Unknown Vote"
        
        if not donor_category.get(row['extending_org_ref']+"-"+row['spine_category_code']):
            donor_category[row['extending_org_ref']+"-"+row['spine_category_code']] = {'value': 0.0,
                            'source': getOrgCode(row['extending_org'], orgcodes),
                            'target': getOrgCode(row['spine_category'], orgcodes)}
        donor_category[row['extending_org_ref']+"-"+row['spine_category_code']]['value']+=float(row['component_total_commitments'])
        
        if not category_vote.get(row['spine_category_code']+"-"+row['vote_code']):
            category_vote[row['spine_category_code']+"-"+row['vote_code']] = {'value': 0.0,
                            'source': getOrgCode(row['spine_category'], orgcodes),                            
                            'target': getOrgCode(row['vote_name'], orgcodes)}
        category_vote[row['spine_category_code']+"-"+row['vote_code']]['value']+=float(row['component_total_commitments'])
        
    return donor_category, category_vote, orgcodes

donor_category, category_vote, orgcodes = getTotalCosts(CSVfilename)

# sort orgcodes...

out={}
out['nodes'] = [{'name': org} for org in sorted(orgcodes['known'], key=orgcodes['known'].get)]
out['links'] = (donor_category.values()+category_vote.values())
print json.dumps(out)
