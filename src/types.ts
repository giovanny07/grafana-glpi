import { DataQuery, DataSourceJsonData } from '@grafana/data';

// ─── Query Types ────────────────────────────────────────────────────────────

export type GlpiQueryType =
  // Tickets
  | 'ticket_summary'
  | 'ticket_trend'
  | 'ticket_list'
  | 'ticket_by_category'
  | 'ticket_by_technician'
  // SLA / ITIL
  | 'sla_compliance'
  | 'sla_breaches'
  | 'resolution_time'
  | 'priority_breakdown'
  // Assets / Stats
  | 'asset_count'
  | 'asset_list'
  | 'user_workload'
  | 'entity_summary'
  | 'satisfaction';

export const QUERY_TYPE_OPTIONS: Array<{ label: string; value: GlpiQueryType; description: string }> = [
  // Tickets
  { value: 'ticket_summary',       label: 'Ticket summary',       description: 'Total tickets grouped by status' },
  { value: 'ticket_trend',         label: 'Ticket trend',         description: 'Ticket volume over time (timeseries)' },
  { value: 'ticket_list',          label: 'Ticket list',          description: 'Raw ticket table with filters' },
  { value: 'ticket_by_category',   label: 'By category',          description: 'Distribution by ITIL category' },
  { value: 'ticket_by_technician', label: 'By technician',        description: 'Workload per user / group' },
  // SLA
  { value: 'sla_compliance',       label: 'SLA compliance',       description: '% tickets resolved within SLA' },
  { value: 'sla_breaches',         label: 'SLA breaches',         description: 'Tickets that exceeded SLA' },
  { value: 'resolution_time',      label: 'Resolution time',      description: 'Avg / p95 resolution time' },
  { value: 'priority_breakdown',   label: 'Priority breakdown',   description: 'Urgency / impact / priority distribution' },
  // Assets
  { value: 'asset_count',          label: 'Asset count',          description: 'Asset totals by type and entity' },
  { value: 'asset_list',           label: 'Asset list',           description: 'Inventory table with filters' },
  { value: 'user_workload',        label: 'User workload',        description: 'Open tickets per technician' },
  { value: 'entity_summary',       label: 'Entity summary',       description: 'Key metrics per GLPI entity' },
  { value: 'satisfaction',         label: 'Satisfaction',         description: 'Average rating from surveys' },
];

// ─── Common Filters ──────────────────────────────────────────────────────────

export interface GlpiFilters {
  entity_id?: number;
  status?: number[];        // GLPI status codes: 1=new 2=assigned 3=planned 4=waiting 5=solved 6=closed
  priority?: number[];      // 1-6
  category_id?: number;
  technician_id?: number;
  group_id?: number;
  ticket_type?: 1 | 2;     // 1=incident 2=request
}

// ─── Per-QueryType options ────────────────────────────────────────────────────

export interface TicketTrendOptions {
  interval: 'hour' | 'day' | 'week' | 'month';
  group_by?: 'status' | 'priority' | 'category' | 'none';
}

export interface SlaComplianceOptions {
  sla_id?: number;
  show_percentage: boolean;
}

export interface ResolutionTimeOptions {
  unit: 'minutes' | 'hours' | 'days';
  show_percentile: boolean;   // show p95 alongside avg
}

export interface AssetOptions {
  itemtype: string;           // Computer, Monitor, NetworkEquipment, etc.
}

// ─── Main Query Interface ─────────────────────────────────────────────────────

export interface GlpiQuery extends DataQuery {
  queryType: GlpiQueryType;
  filters: GlpiFilters;

  // Per-type options (only one is active depending on queryType)
  ticketTrendOptions?: TicketTrendOptions;
  slaOptions?: SlaComplianceOptions;
  resolutionTimeOptions?: ResolutionTimeOptions;
  assetOptions?: AssetOptions;

  // Display
  maxResults?: number;        // for list queries
  groupByEntity?: boolean;    // break down by entity
}

export const DEFAULT_QUERY: Partial<GlpiQuery> = {
  queryType: 'ticket_summary',
  filters: {},
  maxResults: 100,
  groupByEntity: false,
};

// ─── Datasource Config ────────────────────────────────────────────────────────

export interface GlpiDataSourceOptions extends DataSourceJsonData {
  url: string;
  app_token: string;
  default_entity_id?: number;
  verify_ssl: boolean;
  backend_url?: string;       // URL del FastAPI si corre separado; vacío = sidecar local
}

// Campos que van en secureJsonData (nunca llegan al browser después de guardar)
export interface GlpiSecureJsonData {
  user_token?: string;        // Preferred: Personal API token del usuario GLPI
  password?: string;          // Fallback: contraseña (si se usa user+pass)
  username?: string;
}
