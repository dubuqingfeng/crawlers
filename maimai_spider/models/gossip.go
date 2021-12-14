package models

import (
	"github.com/dubuqingfeng/maimai-crawler/db"
)

type Gossip struct {
	ID           string `json:"id" gorm:"primary_key"`
	Username     string `json:"username"`
	Status       int    `json:"status"`
	Major        int    `json:"major"`
	TotalCnt     int    `json:"total_cnt"`
	Text         string `json:"text"`
	Profession   int    `json:"profession"`
	Summary      string `json:"summary"`
	Egid         string `json:"egid"`
	Unlikes      int    `json:"unlikes"`
	Likes        int    `json:"likes"`
	IsFreeze     int    `json:"is_freeze"`
	Crtime       string `json:"crtime"`
	EncodeID     string `json:"encode_id"`
	CrtimeString string `json:"crtime_string"`
	Author       string `json:"author"`
	SearchOrder  int    `json:"search_order"`
	SearchQs     string `json:"search_qs"`
	Avatar       string `json:"avatar"`
	// 额外字段
	GossipUID string `json:"gossip_uid"`
}

type GossipComment struct {
	Real       int         `json:"real"`
	Major      int         `json:"major"`
	Likes      int         `json:"likes"`
	Mmid       string      `json:"mmid"`
	Career     string      `json:"career"`
	Text       string      `json:"text"`
	ReplyText  string      `json:"reply_text"`
	Profession int         `json:"profession"`
	IsTop      int         `json:"is_top"`
	Mylike     int         `json:"mylike"`
	RichText   string      `json:"rich_text"`
	Prefix     string      `json:"prefix"`
	Avatar     string      `json:"avatar"`
	Judge      interface{} `json:"judge"`
	Lz         int         `json:"lz"`
	ID         int         `json:"id"`
	GossipUID  string      `json:"gossip_uid"`
	Name       string      `json:"name"`
	NameColor  string      `json:"name_color,omitempty"`
	// 额外字段
	GossipId int `json:"gossip_id"`
}

const TableGossips = "gossips"
const TableGossipComments = "gossip_comments"

func SaveCommentItem(table string, item GossipComment) {
	if table == "" {
		table = TableGossipComments
	}
	var comment GossipComment
	db := dbs.GetGormDB()
	db.Table(table).Where("id = ?", item.ID).First(&comment)
	defer db.Close()
	if comment.ID == 0 {
		db.Table(table).Create(&item)
		return
	}
}

func SaveGossipItem(table string, item Gossip) {
	if table == "" {
		table = TableGossips
	}
	var gossip Gossip
	db := dbs.GetGormDB()
	db.Table(table).Where("id = ?", item.ID).First(&gossip)
	defer db.Close()
	if gossip.ID == "" || gossip.ID == "0" {
		db.Table(table).Create(&item)
		return
	}
	if gossip.TotalCnt == item.TotalCnt {
		return
	}
	item.GossipUID = gossip.GossipUID
	db.Table(table).Save(&item)
}

// 更新职言列表 ID
func UpdateGossipItemGossipID(id, gossipId, table string) {
	if gossipId == "" {
		return
	}
	if table == "" {
		table = TableGossips
	}
	db := dbs.GetGormDB()
	db.Table(table).Where("id = ?", id).Updates(map[string]interface{}{"gossip_uid": gossipId})
	db.Close()
}

// 获取待更新职言ID 的职言列表
func GetAllEmptyGossipIdItem(table string) []Gossip {
	if table == "" {
		table = TableGossips
	}
	var gossips []Gossip
	db := dbs.GetGormDB()
	db.Table(table).Where("gossip_id_status = 0").Where("gossip_uid = ''").Order("id desc").Find(&gossips)
	db.Close()
	return gossips
}

// 获取需要爬取评论的 items
func GetCrawlCommentsGossipItems(table string) []Gossip {
	if table == "" {
		table = TableGossips
	}
	var gossips []Gossip
	db := dbs.GetGormDB()
	db.Table(table).Where("gossip_status = 0").Order("id desc").Limit(100).Find(&gossips)
	db.Close()
	return gossips
}
