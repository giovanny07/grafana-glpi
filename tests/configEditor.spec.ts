import { test, expect } from '@grafana/plugin-e2e';

test('smoke: should render GLPI config editor', async ({
  createDataSourceConfigPage,
  page,
}) => {
  await createDataSourceConfigPage({ type: 'imagunet-glpi-datasource' });
  await expect(page.getByLabel('GLPI URL')).toBeVisible();
  await expect(page.getByLabel('App Token')).toBeVisible();
  await expect(page.getByLabel('Verify SSL')).toBeVisible();
});

test('config editor should show backend URL field', async ({
  createDataSourceConfigPage,
  page,
}) => {
  await createDataSourceConfigPage({ type: 'imagunet-glpi-datasource' });
  await expect(page.getByLabel('Backend URL')).toBeVisible();
});

test('"Save & test" should succeed with valid provisioned config', async ({
  readProvisionedDataSource,
  createDataSourceConfigPage,
}) => {
  const ds = await readProvisionedDataSource({ fileName: 'datasources.yml' });
  const configPage = await createDataSourceConfigPage({ type: ds.type });
  await expect(configPage.saveAndTest()).toBeOK();
});
