import React, { ChangeEvent } from 'react';
import { InlineField, InlineFieldRow, Input, Switch, SecretInput, FieldSet } from '@grafana/ui';
import { DataSourcePluginOptionsEditorProps } from '@grafana/data';
import { GlpiDataSourceOptions, GlpiSecureJsonData } from '../types';

type Props = DataSourcePluginOptionsEditorProps<GlpiDataSourceOptions, GlpiSecureJsonData>;

export function ConfigEditor({ options, onOptionsChange }: Props) {
  const { jsonData, secureJsonFields, secureJsonData } = options;

  const onJsonDataChange = (key: keyof GlpiDataSourceOptions) => (e: ChangeEvent<HTMLInputElement>) => {
    onOptionsChange({ ...options, jsonData: { ...jsonData, [key]: e.target.value } });
  };

  const onSwitchChange = (key: keyof GlpiDataSourceOptions) => (e: ChangeEvent<HTMLInputElement>) => {
    onOptionsChange({ ...options, jsonData: { ...jsonData, [key]: e.target.checked } });
  };

  const onSecureChange = (key: keyof GlpiSecureJsonData) => (e: ChangeEvent<HTMLInputElement>) => {
    onOptionsChange({
      ...options,
      secureJsonData: { ...secureJsonData, [key]: e.target.value },
    });
  };

  const onResetSecret = (key: keyof GlpiSecureJsonData) => () => {
    onOptionsChange({
      ...options,
      secureJsonFields: { ...secureJsonFields, [key]: false },
      secureJsonData: { ...secureJsonData, [key]: '' },
    });
  };

  return (
    <div>
      <FieldSet label="GLPI connection">
        <InlineFieldRow>
          <InlineField label="GLPI URL" labelWidth={20} tooltip="Base URL of your GLPI instance (e.g. https://glpi.example.com)">
            <Input
              width={50}
              value={jsonData.url || ''}
              onChange={onJsonDataChange('url')}
              placeholder="https://glpi.example.com"
            />
          </InlineField>
        </InlineFieldRow>

        <InlineFieldRow>
          <InlineField label="App token" labelWidth={20} tooltip="GLPI application token (Setup → General → API)">
            <Input
              width={50}
              value={jsonData.app_token || ''}
              onChange={onJsonDataChange('app_token')}
              placeholder="App token from GLPI API settings"
            />
          </InlineField>
        </InlineFieldRow>

        <InlineFieldRow>
          <InlineField label="Verify SSL" labelWidth={20} tooltip="Verify SSL certificate when connecting to GLPI">
            <Switch
              value={jsonData.verify_ssl ?? true}
              onChange={onSwitchChange('verify_ssl')}
            />
          </InlineField>
        </InlineFieldRow>
      </FieldSet>

      <FieldSet label="Authentication (stored encrypted)">
        <InlineFieldRow>
          <InlineField
            label="User token"
            labelWidth={20}
            tooltip="Personal API token from GLPI user profile → Remote access key. Preferred over username/password."
          >
            <SecretInput
              width={50}
              isConfigured={!!secureJsonFields?.user_token}
              value={secureJsonData?.user_token || ''}
              placeholder="User personal API token (recommended)"
              onReset={onResetSecret('user_token')}
              onChange={onSecureChange('user_token')}
            />
          </InlineField>
        </InlineFieldRow>

        <InlineFieldRow>
          <InlineField label="Username" labelWidth={20} tooltip="GLPI username — only used if user token is not set">
            <SecretInput
              width={50}
              isConfigured={!!secureJsonFields?.username}
              value={secureJsonData?.username || ''}
              placeholder="fallback if no user token"
              onReset={onResetSecret('username')}
              onChange={onSecureChange('username')}
            />
          </InlineField>
        </InlineFieldRow>

        <InlineFieldRow>
          <InlineField label="Password" labelWidth={20} tooltip="GLPI password — only used if user token is not set">
            <SecretInput
              width={50}
              isConfigured={!!secureJsonFields?.password}
              value={secureJsonData?.password || ''}
              placeholder="fallback if no user token"
              onReset={onResetSecret('password')}
              onChange={onSecureChange('password')}
            />
          </InlineField>
        </InlineFieldRow>
      </FieldSet>

      <FieldSet label="Advanced">
        <InlineFieldRow>
          <InlineField
            label="Default entity"
            labelWidth={20}
            tooltip="Default GLPI entity ID to filter all queries. Leave empty for root entity."
          >
            <Input
              width={20}
              type="number"
              value={jsonData.default_entity_id ?? ''}
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                onOptionsChange({
                  ...options,
                  jsonData: { ...jsonData, default_entity_id: parseInt(e.target.value, 10) || undefined },
                })
              }
              placeholder="0"
            />
          </InlineField>
        </InlineFieldRow>

        <InlineFieldRow>
          <InlineField
            label="Backend URL"
            labelWidth={20}
            tooltip="URL of the Python FastAPI sidecar. Leave empty to use the default sidecar on port 8765."
          >
            <Input
              width={50}
              value={jsonData.backend_url || ''}
              onChange={onJsonDataChange('backend_url')}
              placeholder="http://localhost:8765 (default sidecar)"
            />
          </InlineField>
        </InlineFieldRow>
      </FieldSet>
    </div>
  );
}
