import React, { ChangeEvent } from 'react';
import { InlineField, InlineFieldRow, Select, Switch, Input, FieldSet } from '@grafana/ui';
import { QueryEditorProps, SelectableValue } from '@grafana/data';
import { DataSource } from '../datasource';
import {
  GlpiDataSourceOptions,
  GlpiQuery,
  GlpiQueryType,
  QUERY_TYPE_OPTIONS,
  TicketTrendOptions,
  SlaComplianceOptions,
  ResolutionTimeOptions,
} from '../types';

type Props = QueryEditorProps<DataSource, GlpiQuery, GlpiDataSourceOptions>;

const TICKET_STATUS_OPTIONS = [
  { label: 'New',      value: 1 },
  { label: 'Assigned', value: 2 },
  { label: 'Planned',  value: 3 },
  { label: 'Waiting',  value: 4 },
  { label: 'Solved',   value: 5 },
  { label: 'Closed',   value: 6 },
];

const PRIORITY_OPTIONS = [
  { label: 'Very low',  value: 1 },
  { label: 'Low',       value: 2 },
  { label: 'Medium',    value: 3 },
  { label: 'High',      value: 4 },
  { label: 'Very high', value: 5 },
  { label: 'Major',     value: 6 },
];

const INTERVAL_OPTIONS: Array<SelectableValue<TicketTrendOptions['interval']>> = [
  { label: 'Hour',  value: 'hour' },
  { label: 'Day',   value: 'day' },
  { label: 'Week',  value: 'week' },
  { label: 'Month', value: 'month' },
];

const TREND_GROUP_OPTIONS: Array<SelectableValue<TicketTrendOptions['group_by']>> = [
  { label: 'None',     value: 'none' },
  { label: 'Status',   value: 'status' },
  { label: 'Priority', value: 'priority' },
  { label: 'Category', value: 'category' },
];

const ASSET_TYPE_OPTIONS = [
  { label: 'Computer',          value: 'Computer' },
  { label: 'Monitor',           value: 'Monitor' },
  { label: 'Network equipment', value: 'NetworkEquipment' },
  { label: 'Printer',           value: 'Printer' },
  { label: 'Phone',             value: 'Phone' },
  { label: 'Software',          value: 'Software' },
];

const TIME_UNIT_OPTIONS: Array<SelectableValue<ResolutionTimeOptions['unit']>> = [
  { label: 'Minutes', value: 'minutes' },
  { label: 'Hours',   value: 'hours' },
  { label: 'Days',    value: 'days' },
];

// Grafana UI Select con isMulti pasa SelectableValue<T> | SelectableValue<T>[]
// dependiendo de la versión — normalizamos siempre a array
function toValues<T>(v: SelectableValue<T> | Array<SelectableValue<T>>): T[] {
  const arr = Array.isArray(v) ? v : [v];
  return arr.map((i) => i.value!).filter((x) => x !== undefined);
}

export function QueryEditor({ query, onChange, onRunQuery }: Props) {
  const q = query;

  const onQueryTypeChange = (v: SelectableValue<GlpiQueryType>) => {
    onChange({ ...q, queryType: v.value! });
    onRunQuery();
  };

  const onFilterNumberChange = (key: keyof typeof q.filters) => (e: ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    onChange({ ...q, filters: { ...q.filters, [key]: isNaN(val) ? undefined : val } });
  };

  const onMultiStatus = (v: SelectableValue<number> | Array<SelectableValue<number>>) => {
    onChange({ ...q, filters: { ...q.filters, status: toValues(v) } });
    onRunQuery();
  };

  const onMultiPriority = (v: SelectableValue<number> | Array<SelectableValue<number>>) => {
    onChange({ ...q, filters: { ...q.filters, priority: toValues(v) } });
    onRunQuery();
  };

  const showTrendOptions = q.queryType === 'ticket_trend';
  const showSlaOptions   = q.queryType === 'sla_compliance' || q.queryType === 'sla_breaches';
  const showResTime      = q.queryType === 'resolution_time';
  const showAssetType    = q.queryType === 'asset_count' || q.queryType === 'asset_list';
  const showMaxResults   = ['ticket_list', 'asset_list', 'sla_breaches'].includes(q.queryType);

  // Defaults seguros para spreads (evita undefined en campos required)
  const trendOpts: TicketTrendOptions = {
    interval: 'day',
    group_by: 'none',
    ...q.ticketTrendOptions,
  };

  const slaOpts: SlaComplianceOptions = {
    show_percentage: true,
    ...q.slaOptions,
  };

  const resOpts: ResolutionTimeOptions = {
    unit: 'hours',
    show_percentile: false,
    ...q.resolutionTimeOptions,
  };

  return (
    <div>
      <FieldSet label="Query">
        <InlineFieldRow>
          <InlineField label="Query type" labelWidth={18} tooltip="What data to fetch from GLPI">
            <Select
              width={36}
              options={QUERY_TYPE_OPTIONS}
              value={q.queryType}
              onChange={onQueryTypeChange}
            />
          </InlineField>

          <InlineField label="Group by entity" labelWidth={18} tooltip="Break down results per GLPI entity">
            <Switch
              value={q.groupByEntity ?? false}
              onChange={(e: ChangeEvent<HTMLInputElement>) => {
                onChange({ ...q, groupByEntity: e.target.checked });
                onRunQuery();
              }}
            />
          </InlineField>
        </InlineFieldRow>
      </FieldSet>

      <FieldSet label="Filters">
        <InlineFieldRow>
          <InlineField label="Entity ID" labelWidth={18} tooltip="GLPI entity ID (overrides datasource default)">
            <Input
              width={12}
              type="number"
              placeholder="default"
              value={q.filters?.entity_id ?? ''}
              onChange={onFilterNumberChange('entity_id')}
              onBlur={onRunQuery}
            />
          </InlineField>

          <InlineField label="Status" labelWidth={12} tooltip="Filter by ticket status">
            <Select
              width={36}
              isMulti
              options={TICKET_STATUS_OPTIONS}
              value={TICKET_STATUS_OPTIONS.filter((o) => q.filters?.status?.includes(o.value))}
              onChange={onMultiStatus}
              placeholder="All statuses"
            />
          </InlineField>
        </InlineFieldRow>

        <InlineFieldRow>
          <InlineField label="Priority" labelWidth={18} tooltip="Filter by priority">
            <Select
              width={36}
              isMulti
              options={PRIORITY_OPTIONS}
              value={PRIORITY_OPTIONS.filter((o) => q.filters?.priority?.includes(o.value))}
              onChange={onMultiPriority}
              placeholder="All priorities"
            />
          </InlineField>

          <InlineField label="Category ID" labelWidth={14} tooltip="GLPI ITIL category ID">
            <Input
              width={12}
              type="number"
              placeholder="all"
              value={q.filters?.category_id ?? ''}
              onChange={onFilterNumberChange('category_id')}
              onBlur={onRunQuery}
            />
          </InlineField>
        </InlineFieldRow>
      </FieldSet>

      {showTrendOptions && (
        <FieldSet label="Trend options">
          <InlineFieldRow>
            <InlineField label="Interval" labelWidth={18}>
              <Select
                width={20}
                options={INTERVAL_OPTIONS}
                value={trendOpts.interval}
                onChange={(v: SelectableValue<TicketTrendOptions['interval']>) =>
                  onChange({ ...q, ticketTrendOptions: { ...trendOpts, interval: v.value! } })
                }
              />
            </InlineField>

            <InlineField label="Group by" labelWidth={14}>
              <Select
                width={20}
                options={TREND_GROUP_OPTIONS}
                value={trendOpts.group_by}
                onChange={(v: SelectableValue<TicketTrendOptions['group_by']>) =>
                  onChange({ ...q, ticketTrendOptions: { ...trendOpts, group_by: v.value! } })
                }
              />
            </InlineField>
          </InlineFieldRow>
        </FieldSet>
      )}

      {showSlaOptions && (
        <FieldSet label="SLA options">
          <InlineFieldRow>
            <InlineField label="SLA ID" labelWidth={18} tooltip="Leave empty to evaluate all SLAs">
              <Input
                width={12}
                type="number"
                placeholder="all SLAs"
                value={slaOpts.sla_id ?? ''}
                onChange={(e: ChangeEvent<HTMLInputElement>) => {
                  const val = parseInt(e.target.value, 10);
                  onChange({ ...q, slaOptions: { ...slaOpts, sla_id: isNaN(val) ? undefined : val } });
                }}
                onBlur={onRunQuery}
              />
            </InlineField>

            <InlineField label="Show %" labelWidth={14} tooltip="Return percentage instead of count">
              <Switch
                value={slaOpts.show_percentage}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  onChange({ ...q, slaOptions: { ...slaOpts, show_percentage: e.target.checked } })
                }
              />
            </InlineField>
          </InlineFieldRow>
        </FieldSet>
      )}

      {showResTime && (
        <FieldSet label="Resolution time options">
          <InlineFieldRow>
            <InlineField label="Unit" labelWidth={18}>
              <Select
                width={20}
                options={TIME_UNIT_OPTIONS}
                value={resOpts.unit}
                onChange={(v: SelectableValue<ResolutionTimeOptions['unit']>) =>
                  onChange({ ...q, resolutionTimeOptions: { ...resOpts, unit: v.value! } })
                }
              />
            </InlineField>

            <InlineField label="Show p95" labelWidth={14} tooltip="Include 95th percentile alongside average">
              <Switch
                value={resOpts.show_percentile}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  onChange({ ...q, resolutionTimeOptions: { ...resOpts, show_percentile: e.target.checked } })
                }
              />
            </InlineField>
          </InlineFieldRow>
        </FieldSet>
      )}

      {showAssetType && (
        <FieldSet label="Asset options">
          <InlineFieldRow>
            <InlineField label="Asset type" labelWidth={18}>
              <Select
                width={36}
                options={ASSET_TYPE_OPTIONS}
                value={q.assetOptions?.itemtype ?? 'Computer'}
                onChange={(v: SelectableValue<string>) =>
                  onChange({ ...q, assetOptions: { itemtype: v.value! } })
                }
              />
            </InlineField>
          </InlineFieldRow>
        </FieldSet>
      )}

      {showMaxResults && (
        <FieldSet label="Display">
          <InlineFieldRow>
            <InlineField label="Max rows" labelWidth={18} tooltip="Maximum number of rows to return">
              <Input
                width={12}
                type="number"
                value={q.maxResults ?? 100}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  onChange({ ...q, maxResults: parseInt(e.target.value, 10) || 100 })
                }
                onBlur={onRunQuery}
              />
            </InlineField>
          </InlineFieldRow>
        </FieldSet>
      )}
    </div>
  );
}
