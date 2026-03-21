import { DataSourcePlugin } from '@grafana/data';
import { DataSource } from './datasource';
import { ConfigEditor } from './components/ConfigEditor';
import { QueryEditor } from './components/QueryEditor';
import { GlpiQuery, GlpiDataSourceOptions } from './types';

export const plugin = new DataSourcePlugin<DataSource, GlpiQuery, GlpiDataSourceOptions>(DataSource)
  .setConfigEditor(ConfigEditor)
  .setQueryEditor(QueryEditor);
