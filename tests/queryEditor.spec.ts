import { test, expect } from '@grafana/plugin-e2e';

test('smoke: should render GLPI query editor', async ({
  panelEditPage,
  readProvisionedDataSource,
}) => {
  const ds = await readProvisionedDataSource({ fileName: 'datasources.yml' });
  await panelEditPage.datasource.set(ds.name);
  await expect(
    panelEditPage.getQueryEditorRow('A').getByRole('combobox', { name: 'Query Type' })
  ).toBeVisible();
});

test('should show filters when query type is ticket_summary', async ({
  panelEditPage,
  readProvisionedDataSource,
}) => {
  const ds = await readProvisionedDataSource({ fileName: 'datasources.yml' });
  await panelEditPage.datasource.set(ds.name);
  const row = panelEditPage.getQueryEditorRow('A');
  await row.getByRole('combobox', { name: 'Query Type' }).click();
  await row.getByText('Ticket Summary').click();
  await expect(row.getByLabel('Entity ID')).toBeVisible();
});

test('should show trend options when query type is ticket_trend', async ({
  panelEditPage,
  readProvisionedDataSource,
}) => {
  const ds = await readProvisionedDataSource({ fileName: 'datasources.yml' });
  await panelEditPage.datasource.set(ds.name);
  const row = panelEditPage.getQueryEditorRow('A');
  await row.getByRole('combobox', { name: 'Query Type' }).click();
  await row.getByText('Ticket Trend').click();
  await expect(row.getByLabel('Interval')).toBeVisible();
});

test('should show SLA options when query type is sla_compliance', async ({
  panelEditPage,
  readProvisionedDataSource,
}) => {
  const ds = await readProvisionedDataSource({ fileName: 'datasources.yml' });
  await panelEditPage.datasource.set(ds.name);
  const row = panelEditPage.getQueryEditorRow('A');
  await row.getByRole('combobox', { name: 'Query Type' }).click();
  await row.getByText('SLA Compliance').click();
  await expect(row.getByLabel('SLA ID')).toBeVisible();
});
