package plugin

import (
	"context"
	"fmt"
	"time"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
	"github.com/grafana/grafana-plugin-sdk-go/backend/instancemgmt"
	"github.com/grafana/grafana-plugin-sdk-go/data"
	"github.com/imagunet/imagunet-glpi-datasource/pkg/models"
)

var (
	_ backend.QueryDataHandler   = (*Datasource)(nil)
	_ backend.CheckHealthHandler = (*Datasource)(nil)
	_ instancemgmt.InstanceDisposer = (*Datasource)(nil)
)

type Datasource struct {
	settings *models.Settings
	client   *BackendClient
}

func NewDatasource(_ context.Context, s backend.DataSourceInstanceSettings) (instancemgmt.Instance, error) {
	settings, err := models.LoadPluginSettings(s)
	if err != nil {
		return nil, fmt.Errorf("load settings: %w", err)
	}

	return &Datasource{
		settings: settings,
		client:   NewBackendClient(settings),
	}, nil
}

func (d *Datasource) Dispose() {}

// QueryData — punto de entrada para todas las queries desde Grafana
func (d *Datasource) QueryData(ctx context.Context, req *backend.QueryDataRequest) (*backend.QueryDataResponse, error) {
	response := backend.NewQueryDataResponse()

	for _, q := range req.Queries {
		response.Responses[q.RefID] = d.query(ctx, q)
	}

	return response, nil
}

func (d *Datasource) query(ctx context.Context, query backend.DataQuery) backend.DataResponse {
	qm, err := models.ParseQuery(query)
	if err != nil {
		return backend.ErrDataResponse(backend.StatusBadRequest, err.Error())
	}

	result, err := d.client.Query(ctx, qm)
	if err != nil {
		return backend.ErrDataResponse(backend.StatusInternal, err.Error())
	}

	frame, err := responseToFrame(string(qm.QueryType), result)
	if err != nil {
		return backend.ErrDataResponse(backend.StatusInternal, err.Error())
	}

	return backend.DataResponse{Frames: data.Frames{frame}}
}

// responseToFrame convierte BackendResponse (columnas + filas) a un data.Frame de Grafana
func responseToFrame(queryType string, resp *BackendResponse) (*data.Frame, error) {
	frame := data.NewFrame(queryType)

	// Construir campos tipados según la definición de columnas
	fields := make([]*data.Field, len(resp.Columns))
	for i, col := range resp.Columns {
		switch col.Type {
		case "time":
			fields[i] = data.NewField(col.Name, nil, []time.Time{})
		case "number":
			fields[i] = data.NewField(col.Name, nil, []*float64{})
		default: // "string" y cualquier otro
			fields[i] = data.NewField(col.Name, nil, []*string{})
		}
	}

	// Rellenar filas
	for _, row := range resp.Rows {
		if len(row) != len(resp.Columns) {
			continue // fila malformada, saltar
		}
		for i, col := range resp.Columns {
			val := row[i]
			switch col.Type {
			case "time":
				switch v := val.(type) {
				case string:
					t, err := time.Parse(time.RFC3339, v)
					if err == nil {
						fields[i].Append(t)
					} else {
						fields[i].Append(time.Time{})
					}
				default:
					fields[i].Append(time.Time{})
				}
			case "number":
				switch v := val.(type) {
				case float64:
					fields[i].Append(&v)
				case nil:
					fields[i].Append((*float64)(nil))
				default:
					fields[i].Append((*float64)(nil))
				}
			default: // string
				switch v := val.(type) {
				case string:
					fields[i].Append(&v)
				case nil:
					fields[i].Append((*string)(nil))
				default:
					s := fmt.Sprintf("%v", v)
					fields[i].Append(&s)
				}
			}
		}
	}

	frame.Fields = fields
	return frame, nil
}

// CheckHealth — botón "Save & Test" en la configuración del datasource
func (d *Datasource) CheckHealth(ctx context.Context, req *backend.CheckHealthRequest) (*backend.CheckHealthResult, error) {
	settings, err := models.LoadPluginSettings(*req.PluginContext.DataSourceInstanceSettings)
	if err != nil {
		return &backend.CheckHealthResult{
			Status:  backend.HealthStatusError,
			Message: "Unable to load settings",
		}, nil
	}

	if settings.Plugin.URL == "" {
		return &backend.CheckHealthResult{
			Status:  backend.HealthStatusError,
			Message: "GLPI URL is required",
		}, nil
	}

	if settings.Plugin.AppToken == "" {
		return &backend.CheckHealthResult{
			Status:  backend.HealthStatusError,
			Message: "App token is required",
		}, nil
	}

	if settings.Secrets.UserToken == "" && settings.Secrets.Username == "" {
		return &backend.CheckHealthResult{
			Status:  backend.HealthStatusError,
			Message: "User token or username/password is required",
		}, nil
	}

	client := NewBackendClient(settings)
	if err := client.Health(ctx); err != nil {
		return &backend.CheckHealthResult{
			Status:  backend.HealthStatusError,
			Message: fmt.Sprintf("Connection failed: %s", err.Error()),
		}, nil
	}

	return &backend.CheckHealthResult{
		Status:  backend.HealthStatusOk,
		Message: fmt.Sprintf("Connected to GLPI at %s", settings.Plugin.URL),
	}, nil
}
