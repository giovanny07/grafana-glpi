package models

import (
	"encoding/json"
	"fmt"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
)

type PluginSettings struct {
	URL             string `json:"url"`
	AppToken        string `json:"app_token"`
	DefaultEntityID int    `json:"default_entity_id"`
	VerifySSL       bool   `json:"verify_ssl"`
	BackendURL      string `json:"backend_url"`
}

type SecureSettings struct {
	UserToken string
	Username  string
	Password  string
}

type Settings struct {
	Plugin  PluginSettings
	Secrets SecureSettings
}

func LoadPluginSettings(source backend.DataSourceInstanceSettings) (*Settings, error) {
	settings := &Settings{}
	if err := json.Unmarshal(source.JSONData, &settings.Plugin); err != nil {
		return nil, fmt.Errorf("could not unmarshal PluginSettings json: %w", err)
	}
	settings.Secrets = SecureSettings{
		UserToken: source.DecryptedSecureJSONData["user_token"],
		Username:  source.DecryptedSecureJSONData["username"],
		Password:  source.DecryptedSecureJSONData["password"],
	}
	return settings, nil
}
