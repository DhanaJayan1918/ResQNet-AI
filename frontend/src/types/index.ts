/**
 * ResQNet AI - TypeScript Type Definitions
 * Core types matching backend Pydantic models.
 */

// ---- Enums ----

export type UserRole =
  | 'citizen' | 'volunteer' | 'hospital' | 'shelter_manager'
  | 'field_officer' | 'coordinator' | 'gov_admin' | 'super_admin';

export type IncidentType =
  | 'flood' | 'earthquake' | 'wildfire' | 'medical' | 'infrastructure'
  | 'shelter_overload' | 'power_outage' | 'evacuation' | 'chemical'
  | 'collapse' | 'landslide' | 'cyclone' | 'other';

export type IncidentStatus =
  | 'new' | 'processing' | 'verified' | 'assigned'
  | 'in_progress' | 'resolved' | 'closed' | 'duplicate';

export type Severity = 'low' | 'moderate' | 'high' | 'critical' | 'catastrophic';
export type Urgency = 'low' | 'medium' | 'high' | 'immediate';
export type ResourceType =
  | 'ambulance' | 'rescue_boat' | 'medical_team' | 'volunteer_team'
  | 'food_supply' | 'water_supply' | 'medical_kit' | 'shelter'
  | 'generator' | 'police_unit' | 'fire_unit' | 'helicopter' | 'drone';
export type ResourceStatus = 'available' | 'assigned' | 'in_transit' | 'on_scene' | 'maintenance' | 'offline';

// ---- User ----

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  phone?: string;
  organization?: string;
  is_active: boolean;
  permissions: string[];
  created_at: string;
  last_login?: string;
}

// ---- Auth ----

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  organization?: string;
  role?: UserRole;
}

// ---- Incident ----

export interface GeoJSONPoint {
  type: 'Point';
  coordinates: [number, number]; // [lng, lat]
}

export interface IncidentLocation extends GeoJSONPoint {
  address?: string;
  landmark?: string;
  region?: string;
}

export interface VulnerablePopulations {
  children: number;
  elderly: number;
  disabled: number;
  pregnant: number;
  chronic_illness: number;
}

export interface ResourceRequirement {
  resource_type: string;
  quantity: number;
  urgency: Urgency;
}

export interface AIAnalysis {
  incident_type: IncidentType;
  severity: Severity;
  urgency: Urgency;
  people_affected: number;
  vulnerable_populations: VulnerablePopulations;
  resource_requirements: ResourceRequirement[];
  confidence_score: number;
  reasoning: string;
  processed_at?: string;
}

export interface ImpactEstimate {
  medical_demand: number;
  shelter_demand: number;
  food_water_demand: number;
  rescue_demand: number;
  infrastructure_damage_score: number;
  estimated_duration_hours: number;
}

export interface PriorityFactors {
  severity_score: number;
  urgency_score: number;
  people_affected_score: number;
  vulnerability_score: number;
  resource_scarcity_score: number;
  accessibility_score: number;
  shelter_load_score: number;
  hospital_load_score: number;
}

export interface Priority {
  score: number;
  rank: number;
  factors: PriorityFactors;
  explanation: string;
  calculated_at?: string;
}

export interface TimelineEvent {
  event: string;
  timestamp: string;
  actor: string;
  details?: string;
}

export interface Incident {
  id: string;
  incident_id: string;
  status: IncidentStatus;
  source: {
    type: string;
    reporter_name?: string;
    reporter_contact?: string;
    submission_channel: string;
  };
  raw_report: {
    text: string;
    images: string[];
    metadata: Record<string, unknown>;
  };
  location: IncidentLocation;
  ai_analysis: AIAnalysis;
  impact_estimate: ImpactEstimate;
  priority: Priority;
  duplicate_group_id?: string;
  assigned_resources: AssignedResource[];
  response_plan: ResponsePlan;
  timeline: TimelineEvent[];
  created_at: string;
  updated_at: string;
}

export interface AssignedResource {
  resource_id: string;
  assigned_at: string;
  eta_minutes: number;
  status: string;
}

export interface ResponsePlan {
  recommended_actions: string[];
  resource_assignments: Record<string, unknown>[];
  expected_impact: string;
  alternatives: string[];
  explanation: string;
}

// ---- Resource ----

export interface Resource {
  id: string;
  resource_id: string;
  type: ResourceType;
  name: string;
  status: ResourceStatus;
  location: {
    type: string;
    coordinates: [number, number];
    last_updated: string;
  };
  capacity: {
    total: number;
    current_load: number;
    unit: string;
  };
  capabilities: string[];
  assigned_incident_id?: string;
  organization: string;
  contact?: string;
}

// ---- Shelter ----

export interface Shelter {
  id: string;
  shelter_id: string;
  name: string;
  address: string;
  location: GeoJSONPoint;
  total_capacity: number;
  current_occupancy: number;
  occupancy_percentage: number;
  available_capacity: number;
  status: 'open' | 'full' | 'closed' | 'evacuating';
  facilities: string[];
  contact_person: string;
  supplies: {
    food_days_remaining: number;
    water_days_remaining: number;
    medical_kits: number;
    blankets: number;
  };
}

// ---- Hospital ----

export interface Hospital {
  id: string;
  hospital_id: string;
  name: string;
  address: string;
  location: GeoJSONPoint;
  total_beds: number;
  available_beds: number;
  icu_beds_total: number;
  icu_beds_available: number;
  er_capacity: number;
  er_current_load: number;
  er_load_percent: number;
  bed_utilization_percent: number;
  specialties: string[];
  ambulances_available: number;
  status: 'operational' | 'limited' | 'overwhelmed' | 'evacuating' | 'offline';
}

// ---- Analytics ----

export interface DashboardOverview {
  total_incidents: number;
  active_incidents: number;
  critical_incidents: number;
  resolved_today: number;
  total_resources: number;
  available_resources: number;
  deployed_resources: number;
  total_shelters: number;
  shelter_occupancy_avg: number;
  total_hospitals: number;
  hospital_bed_utilization_avg: number;
  avg_response_time_minutes: number;
  incidents_last_24h: number;
}

// ---- API Response ----

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface MessageResponse {
  message: string;
  success: boolean;
}
