/**
 * ResQNet AI - App Constants
 */

export const INCIDENT_TYPE_LABELS: Record<string, string> = {
  flood: 'Flood',
  earthquake: 'Earthquake',
  wildfire: 'Wildfire',
  medical: 'Medical Emergency',
  infrastructure: 'Infrastructure Failure',
  shelter_overload: 'Shelter Overload',
  power_outage: 'Power Outage',
  evacuation: 'Evacuation',
  chemical: 'Chemical Hazard',
  collapse: 'Building Collapse',
  landslide: 'Landslide',
  cyclone: 'Cyclone',
  other: 'Other',
};

export const INCIDENT_TYPE_ICONS: Record<string, string> = {
  flood: '🌊',
  earthquake: '🌍',
  wildfire: '🔥',
  medical: '🏥',
  infrastructure: '🏗️',
  shelter_overload: '🏠',
  power_outage: '⚡',
  evacuation: '🚨',
  chemical: '☣️',
  collapse: '🏚️',
  landslide: '⛰️',
  cyclone: '🌀',
  other: '⚠️',
};

export const SEVERITY_COLORS: Record<string, string> = {
  low: '#22c55e',
  moderate: '#eab308',
  high: '#f97316',
  critical: '#ef4444',
  catastrophic: '#dc2626',
};

export const STATUS_LABELS: Record<string, string> = {
  new: 'New',
  processing: 'Processing',
  verified: 'Verified',
  assigned: 'Assigned',
  in_progress: 'In Progress',
  resolved: 'Resolved',
  closed: 'Closed',
  duplicate: 'Duplicate',
};

export const RESOURCE_TYPE_ICONS: Record<string, string> = {
  ambulance: '🚑',
  rescue_boat: '🚤',
  medical_team: '👨‍⚕️',
  volunteer_team: '🤝',
  food_supply: '🍞',
  water_supply: '💧',
  medical_kit: '🩺',
  shelter: '🏠',
  generator: '🔋',
  police_unit: '👮',
  fire_unit: '🚒',
  helicopter: '🚁',
  drone: '🛸',
};

export const ROLE_LABELS: Record<string, string> = {
  citizen: 'Citizen',
  volunteer: 'Volunteer',
  hospital: 'Hospital',
  shelter_manager: 'Shelter Manager',
  field_officer: 'Field Officer',
  coordinator: 'Emergency Coordinator',
  gov_admin: 'Government Admin',
  super_admin: 'Super Admin',
};
