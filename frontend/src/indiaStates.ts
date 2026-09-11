import type { IndiaAdministrativeOption, IndiaAdministrativeOptions } from './types'

// Official names of India's 28 States and 8 Union Territories. This small,
// versioned directory is bundled so the first location control never waits on
// a third-party boundary service. Source: Government of India, National Portal
// (https://knowindia.india.gov.in/states-uts/). Boundary geometry is still
// retrieved and evidenced separately when a district is selected.
const stateNames = [
  'Andaman and Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam',
  'Bihar', 'Chandigarh', 'Chhattisgarh', 'Dadra and Nagar Haveli and Daman and Diu',
  'Delhi', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jammu and Kashmir',
  'Jharkhand', 'Karnataka', 'Kerala', 'Ladakh', 'Lakshadweep', 'Madhya Pradesh',
  'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha',
  'Puducherry', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana',
  'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
] as const

const slug = (value: string) => value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')

export const INDIA_STATES: IndiaAdministrativeOption[] = stateNames.map((name) => ({
  id: `state:${slug(name)}`,
  name,
  admin_level: '4',
}))

export const INDIA_STATES_RESPONSE: IndiaAdministrativeOptions = {
  status: 'AVAILABLE',
  level: 'state',
  options: INDIA_STATES,
  confidence: 'HIGH',
  limitations: ['State and Union Territory names are bundled from the Government of India directory for instant navigation.'],
  data_provenance: [{
    source_id: 'GOV_IN_STATES_UTS_DIRECTORY',
    source_name: 'Government of India States and Union Territories directory',
    source_url: 'https://knowindia.india.gov.in/states-uts/',
    data_type: 'VERIFIED',
    confidence: 'HIGH',
  }],
}
