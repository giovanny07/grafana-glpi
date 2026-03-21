package models

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
)

// GlpiQueryType — debe coincidir exactamente con src/types.ts
type GlpiQueryType string

const (
	QueryTicketSummary      GlpiQueryType = "ticket_summary"
	QueryTicketTrend        GlpiQueryType = "ticket_trend"
	QueryTicketList         GlpiQueryType = "ticket_list"
	QueryTicketByCategory   GlpiQueryType = "ticket_by_category"
	QueryTicketByTechnician GlpiQueryType = "ticket_by_technician"
	QuerySLACompliance      GlpiQueryType = "sla_compliance"
	QuerySLABreaches        GlpiQueryType = "sla_breaches"
	QueryResolutionTime     GlpiQueryType = "resolution_time"
	QueryPriorityBreakdown  GlpiQueryType = "priority_breakdown"
	QueryAssetCount         GlpiQueryType = "asset_count"
	QueryAssetList          GlpiQueryType = "asset_list"
	QueryUserWorkload       GlpiQueryType = "user_workload"
	QueryEntitySummary      GlpiQueryType = "entity_summary"
	QuerySatisfaction       GlpiQueryType = "satisfaction"
)

// GlpiFilters — filtros comunes a todos los query types
type GlpiFilters struct {
	EntityID     *int  `json:"entity_id,omitempty"`
	Status       []int `json:"status,omitempty"`
	Priority     []int `json:"priority,omitempty"`
	CategoryID   *int  `json:"category_id,omitempty"`
	TechnicianID *int  `json:"technician_id,omitempty"`
	GroupID      *int  `json:"group_id,omitempty"`
	TicketType   *int  `json:"ticket_type,omitempty"`
}

type TicketTrendOptions struct {
	Interval string `json:"interval"` // hour|day|week|month
	GroupBy  string `json:"group_by"` // none|status|priority|category
}

type SlaOptions struct {
	SlaID          *int `json:"sla_id,omitempty"`
	ShowPercentage bool `json:"show_percentage"`
}

type ResolutionTimeOptions struct {
	Unit           string `json:"unit"`            // minutes|hours|days
	ShowPercentile bool   `json:"show_percentile"` // incluir p95
}

type AssetOptions struct {
	Itemtype string `json:"itemtype"` // Computer|Monitor|NetworkEquipment|...
}

// GlpiQueryModel — estructura completa del query desde el frontend
type GlpiQueryModel struct {
	QueryType   GlpiQueryType `json:"queryType"`
	Filters     GlpiFilters   `json:"filters"`
	GroupByEntity bool        `json:"groupByEntity"`
	MaxResults  int           `json:"maxResults"`

	TicketTrendOptions    *TicketTrendOptions    `json:"ticketTrendOptions,omitempty"`
	SlaOptions            *SlaOptions            `json:"slaOptions,omitempty"`
	ResolutionTimeOptions *ResolutionTimeOptions `json:"resolutionTimeOptions,omitempty"`
	AssetOptions          *AssetOptions          `json:"assetOptions,omitempty"`

	// Inyectados por el Go (no vienen del frontend)
	TimeFrom time.Time `json:"-"`
	TimeTo   time.Time `json:"-"`
}

func ParseQuery(query backend.DataQuery) (*GlpiQueryModel, error) {
	var qm GlpiQueryModel
	if err := json.Unmarshal(query.JSON, &qm); err != nil {
		return nil, fmt.Errorf("json unmarshal query: %w", err)
	}

	qm.TimeFrom = query.TimeRange.From
	qm.TimeTo = query.TimeRange.To

	if qm.MaxResults <= 0 {
		qm.MaxResults = 100
	}

	return &qm, nil
}
