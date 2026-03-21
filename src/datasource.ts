import { DataSourceInstanceSettings, CoreApp } from '@grafana/data';
import { DataSourceWithBackend } from '@grafana/runtime';

import { GlpiQuery, GlpiDataSourceOptions, DEFAULT_QUERY } from './types';

export class DataSource extends DataSourceWithBackend<GlpiQuery, GlpiDataSourceOptions> {
  constructor(instanceSettings: DataSourceInstanceSettings<GlpiDataSourceOptions>) {
    super(instanceSettings);
  }

  filterQuery(query: GlpiQuery): boolean {
    return !!query.queryType;
  }

  getDefaultQuery(_app: CoreApp): Partial<GlpiQuery> {
    return DEFAULT_QUERY;
  }
}
