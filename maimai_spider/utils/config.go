package utils

import "github.com/jinzhu/configor"

var MySQLConfigs map[string]MySQLDSN

type MySQLDSN struct {
	Name string
	DSN  string
}

type MySQLDB struct {
	Read     MySQLDSN
	Write    MySQLDSN
	Timezone string
}

var Config = struct {
	GlobalDatabase    MySQLDB
	GossipsIsLoadMore bool
	Cookie            string
	Auth              struct {
		CSRF        string
		CSRFToken   string
		U           string
		AccessToken string
	}
}{}

func InitConfig(files string) error {
	return configor.Load(&Config, files)
}

func SetMySQLConfigs() {
	MySQLConfigs = make(map[string]MySQLDSN)
	AddDatabaseConfig(Config.GlobalDatabase, MySQLConfigs)
}

func AddDatabaseConfig(value MySQLDB, configs map[string]MySQLDSN) {
	if value.Read.DSN != "" && value.Read.Name != "" {
		configs[value.Read.Name] = value.Read
	}
	if value.Write.DSN != "" && value.Write.Name != "" {
		configs[value.Write.Name] = value.Write
	}
}
