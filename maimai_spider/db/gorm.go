package dbs

import (
	"github.com/dubuqingfeng/maimai-crawler/utils"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
	log "github.com/sirupsen/logrus"
)

func GetGormDB() *gorm.DB {
	db, err := gorm.Open("mysql", utils.Config.GlobalDatabase.Read.DSN)
	if err != nil {
		log.Error(err)
		return nil
	}
	return db
}
