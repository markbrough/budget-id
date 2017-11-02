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
        if row['spine_code'] == "":
            row['spine_code'] = "unknown-spine"
            row['spine_description'] = "Unknown spine category"

        if row['vote_code'] == "":
            row['vote_code'] = "unknown-vote"
            row['vote_name'] = "Unknown Vote"
        
        if not donor_category.get(row['dac_sector_code']+"-"+row['spine_code']):
            donor_category[row['dac_sector_code']+"-"+row['spine_code']] = {'value': 0.0,
                            'source': getOrgCode(row['dac_sector_code'], orgcodes),
                            'target': getOrgCode(row['spine_description'], orgcodes)}
        donor_category[row['dac_sector_code']+"-"+row['spine_code']]['value']+=float(row['component_total_commitments'])

    return donor_category, orgcodes

donor_category, orgcodes = getTotalCosts(CSVfilename)

# sort orgcodes...

out={}
out['nodes'] = [{'name': org} for org in sorted(orgcodes['known'], key=orgcodes['known'].get)]
out['links'] = (donor_category.values())
print json.dumps(out)
