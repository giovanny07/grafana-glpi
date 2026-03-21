package plugin

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/imagunet/imagunet-glpi-datasource/pkg/models"
)

const defaultBackendURL = "http://localhost:8765"

// BackendClient llama al microservicio FastAPI Python
type BackendClient struct {
	httpClient *http.Client
	baseURL    string
	settings   *models.Settings
}

func NewBackendClient(settings *models.Settings) *BackendClient {
	baseURL := settings.Plugin.BackendURL
	if baseURL == "" {
		baseURL = defaultBackendURL
	}

	return &BackendClient{
		httpClient: &http.Client{Timeout: 30 * time.Second},
		baseURL:    baseURL,
		settings:   settings,
	}
}

// BackendRequest es el payload que enviamos al FastAPI
type BackendRequest struct {
	QueryType     string                  `json:"query_type"`
	Filters       models.GlpiFilters      `json:"filters"`
	GroupByEntity bool                    `json:"group_by_entity"`
	MaxResults    int                     `json:"max_results"`
	TimeFrom      string                  `json:"time_from"` // RFC3339
	TimeTo        string                  `json:"time_to"`   // RFC3339

	// Credenciales (el Go las inyecta desde secureJsonData)
	GlpiURL   string `json:"glpi_url"`
	AppToken  string `json:"app_token"`
	UserToken string `json:"user_token,omitempty"`
	Username  string `json:"username,omitempty"`
	Password  string `json:"password,omitempty"`
	VerifySSL bool   `json:"verify_ssl"`

	// Opciones por tipo
	TrendOptions      *models.TicketTrendOptions    `json:"trend_options,omitempty"`
	SlaOptions        *models.SlaOptions            `json:"sla_options,omitempty"`
	ResolutionOptions *models.ResolutionTimeOptions `json:"resolution_options,omitempty"`
	AssetOptions      *models.AssetOptions          `json:"asset_options,omitempty"`
}

// BackendResponse es lo que devuelve el FastAPI
type BackendResponse struct {
	Columns []ColumnDef       `json:"columns"`
	Rows    [][]interface{}   `json:"rows"`
	Meta    map[string]string `json:"meta,omitempty"`
	Error   string            `json:"error,omitempty"`
}

type ColumnDef struct {
	Name string `json:"name"`
	Type string `json:"type"` // "time"|"number"|"string"
}

func (c *BackendClient) Query(ctx context.Context, qm *models.GlpiQueryModel) (*BackendResponse, error) {
	req := BackendRequest{
		QueryType:     string(qm.QueryType),
		Filters:       qm.Filters,
		GroupByEntity: qm.GroupByEntity,
		MaxResults:    qm.MaxResults,
		TimeFrom:      qm.TimeFrom.Format(time.RFC3339),
		TimeTo:        qm.TimeTo.Format(time.RFC3339),

		GlpiURL:   c.settings.Plugin.URL,
		AppToken:  c.settings.Plugin.AppToken,
		UserToken: c.settings.Secrets.UserToken,
		Username:  c.settings.Secrets.Username,
		Password:  c.settings.Secrets.Password,
		VerifySSL: c.settings.Plugin.VerifySSL,

		TrendOptions:      qm.TicketTrendOptions,
		SlaOptions:        qm.SlaOptions,
		ResolutionOptions: qm.ResolutionTimeOptions,
		AssetOptions:      qm.AssetOptions,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost,
		c.baseURL+"/query", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("create http request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("http request to python backend: %w", err)
	}
	defer func() { _ = resp.Body.Close() }()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response body: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("backend returned %d: %s", resp.StatusCode, string(respBody))
	}

	var result BackendResponse
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("unmarshal response: %w", err)
	}

	if result.Error != "" {
		return nil, fmt.Errorf("backend error: %s", result.Error)
	}

	return &result, nil
}

// Health verifica que el FastAPI esté vivo y pueda conectar con GLPI
func (c *BackendClient) Health(ctx context.Context) error {
	type healthReq struct {
		GlpiURL   string `json:"glpi_url"`
		AppToken  string `json:"app_token"`
		UserToken string `json:"user_token,omitempty"`
		Username  string `json:"username,omitempty"`
		Password  string `json:"password,omitempty"`
		VerifySSL bool   `json:"verify_ssl"`
	}

	req := healthReq{
		GlpiURL:   c.settings.Plugin.URL,
		AppToken:  c.settings.Plugin.AppToken,
		UserToken: c.settings.Secrets.UserToken,
		Username:  c.settings.Secrets.Username,
		Password:  c.settings.Secrets.Password,
		VerifySSL: c.settings.Plugin.VerifySSL,
	}

	body, _ := json.Marshal(req)
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost,
		c.baseURL+"/health", bytes.NewReader(body))
	if err != nil {
		return err
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("python backend unreachable: %w", err)
	}
	defer func() { _ = resp.Body.Close() }()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("health check failed (%d): %s", resp.StatusCode, string(b))
	}

	return nil
}
