from lxml import etree
import unicodecsv

CCCSV = 'crs_cc.csv'
XMLfiles = [{ 'name':'DFATD', 
              'filename': 'dfatd/dfatd-TZ.xml' },
            { 'name':'Sida', 
              'filename': 'sida/sida-TZ.xml' },
            { 'name':'DFID', 
              'filename': 'dfid/dfid-TZ.xml' }]
CSVfilename = 'donors-data.csv'

# Load DFID budget ID data.
# For each activity, add capital-spend and country-budget-items

csvfieldnames = [
                'iati_identifier',
                'extending_org', 
                'extending_org_ref',
                'spine_category_code',
                'spine_category',
                'spine_sector_code',
                'spine_sector',
                'spine_code', 
                'spine_description', 
                'title', 
                'description', 
                'vote_code', 
                'vote_name', 
                'total_disbursements', 
                'component_total_disbursements', 
                'total_commitments',
                'component_total_commitments', 
                'currency',
                'original_total_disbursements',
                'original_total_commitments',
                'start',
                'end',
                'issue',
                'howmany_subcomponents',
                'subcomponent_nr',
                'num_sectors',
                'sector_nr',
                'dac_sector_code',
                ]

def getCRSSpineMapping(filename):
    # Load file
    # Get a dict of CRS code => Spine code
    crsspine_file = open(filename)
    crsspine_rows = unicodecsv.DictReader(crsspine_file)
    #print crsspine_rows.fieldnames
    sectors = {}
    for row in crsspine_rows:
        spinedata = {
                      'spine_code': row['Trial CC code'],
                      'spine_description': row['Function'],
                      'spine_category_code': row['Category code'],
                      'spine_category': row['Category of Government'],
                      'spine_sector_code': row['Sector code'],
                      'spine_sector': row['Sector'],
                    }
        if not sectors.get(row['CRS Code']):
            sectors[row['CRS Code']] = {
                                         'mappings': [],
                                         'num_spine_codes': row['Ccs'], 
                                        }
        sectors[row['CRS Code']]['mappings'].append(spinedata)
    return sectors

def make_project_sector_row(activity_data, sector, crs_spine_mapping, 
                                csvwriter, num_sectors, thissector_num):

    sector_code = sector.xpath("@code")[0]

    # Correct for possibility of missing percentages, with multiple sectors
    if not sector.xpath("@percentage"):
        pct = 100.00/float(num_sectors)
    else:
        pct = float(sector.xpath("@percentage")[0])

    spine_codes = crs_spine_mapping[sector_code]

    count = 1
    for spine in spine_codes['mappings']:
        if len(spine_codes['mappings'])>1:
            divider = pct/float(len(spine_codes['mappings']))/100.00
            issue = "Multiple"
        else:
            divider = pct/100.00
            issue = "No issue"
        if spine['spine_code'] == "":
            issue = "No spine code"
        
        #FIXME: ADJUST FOR CURRENCY
        csvwriter.writerow({
                'iati_identifier': activity_data['iati-identifier'],
                'extending_org': activity_data['extending_org'], 
                'extending_org_ref': activity_data['extending_org_ref'], 
                'spine_category_code': spine['spine_category_code'],
                'spine_category': spine['spine_category'],
                'spine_sector_code': spine['spine_sector_code'],
                'spine_sector': spine['spine_sector'],
                'spine_code': spine['spine_code'], 
                'spine_description': spine['spine_description'], 
                'title': activity_data['title'], 
                'description': activity_data['description'], 
                'vote_code': "", 
                'vote_name': "", 
                'total_disbursements': activity_data['total_disbursements'], 
                'component_total_disbursements': activity_data['total_disbursements']*divider, 
                'total_commitments': activity_data['total_commitments'],
                'component_total_commitments': activity_data['total_commitments']*divider, 
                'currency': activity_data['currency'],
                'original_total_disbursements': activity_data['original_total_disbursements'],
                'original_total_commitments': activity_data['original_total_commitments'],
                'start': activity_data['start'],
                'end': activity_data['end'],
                'issue': issue,
                'howmany_subcomponents': spine_codes['num_spine_codes'],
                'subcomponent_nr': count,
                'num_sectors': num_sectors,
                'sector_nr': thissector_num,
                'dac_sector_code': sector_code,
                })
        count +=1

def get_td(activity, td, attr="text()"):
    en_td = activity.xpath(td+"[@xml:lang='en']/"+attr+"[1]")
    if en_td:
        return en_td[0]
    first_td = activity.xpath(td+"/"+attr+"[1]")
    if first_td:
        return first_td[0]
    return ""

def get_date(activity, startend):
    planned = activity.xpath("activity-date[@type='"+startend+"-planned']")
    actual = activity.xpath("activity-date[@type='"+startend+"-actual']")
    if planned:
        date = planned[0]
    elif actual:
        date = actual[0]
    else:
        return ""
    if date.xpath('@iso-date'):
        return date.xpath('@iso-date')[0]
    else:
        return date.xpath('text()')[0]

def get_DAC_sectors(activity):
    dac_sectors = activity.xpath('sector[@vocabulary="DAC"]')
    if dac_sectors: return dac_sectors
    none_sectors = activity.xpath('sector[not(@vocabulary)]')
    if none_sectors: return none_sectors
    else: return []

def getTotalCommitments(activity, extending_org_ref):
    commitments = activity.xpath("sum(transaction[transaction-type/@code='C']/value/text())")
    if commitments>0: 
        return commitments
    planned_disb = activity.xpath("sum(planned-disbursement/value/text())")
    return planned_disb

def getCurrency(activity):
    if activity.xpath('@default-currency'): 
        return activity.xpath('@default-currency')[0]
    # This actually always finds the currency for DFID, Sida and DFATD, so no 
    # need to look for other cases for now!

def USDconvert(currency):
    # Just used xe.com/ucc on 2014-01-23, sorry :(
    currency_to_dollar = {'GBP': 1.66362,
                          'CAD': 0.900697,
                          'USD': 1.00}
    return currency_to_dollar[currency]

def convertCurrency(currency, value):
    value = value*USDconvert(currency)
    return value

def parse_document(thefile, csvwriter, crs_spine_mapping):
    donor_data = etree.parse(thefile['filename'])
    donor_activities = donor_data.xpath('/iati-activities/iati-activity')

    for activity in donor_activities:
        activity_data = {}
        activity_data['iati-identifier'] = activity.xpath('iati-identifier/text()')[0]
        activity_data['title'] = get_td(activity, "title")
        activity_data['description'] = get_td(activity, "description")
        activity_data['extending_org'] = get_td(activity, 'participating-org[@role="Extending"]')
        activity_data['extending_org_ref'] = get_td(activity, 'participating-org[@role="Extending"]', '@ref')

        activity_data['currency'] = getCurrency(activity)
        activity_data['original_total_commitments'] = getTotalCommitments(activity, activity_data['extending_org_ref'])
        activity_data['original_total_disbursements'] = activity.xpath("sum(transaction[transaction-type/@code='D']/value/text())")

        activity_data['total_disbursements'] = convertCurrency(
                activity_data['currency'],
                activity_data['original_total_disbursements']
                                                                )
        activity_data['total_commitments'] = convertCurrency(
                activity_data['currency'],
                activity_data['original_total_commitments']
        )
        activity_data['start'] = get_date(activity, 'start')
        activity_data['end'] = get_date(activity, 'end')
        
        sectors = get_DAC_sectors(activity)

        if len(sectors)>0:
            for thissector_num, sector in enumerate(sectors):
                make_project_sector_row(activity_data, 
                                        sector, 
                                        crs_spine_mapping,
                                        csvwriter,
                                        len(sectors),
                                        thissector_num+1)
        else:
            print "WARNING: No DAC sectors for project", activity_data['iati-identifier'], "ignoring"

def run():
    
    print "Starting up..."
    # Load CC-CRS mapping
    crs_spine_mapping = getCRSSpineMapping(CCCSV)

    # Setup output file
    csvoutput_file = open(CSVfilename, 'wb')
    csvwriter = unicodecsv.DictWriter(csvoutput_file, csvfieldnames)
    csvwriter.writerow(dict([(k, k) for k in csvfieldnames]))

    for thefile in XMLfiles:
        parse_document(thefile, csvwriter, crs_spine_mapping)

    csvoutput_file.close()
    print "Done"

run()
