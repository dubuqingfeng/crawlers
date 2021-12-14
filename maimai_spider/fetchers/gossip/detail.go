package gossip

import (
	"fmt"
	"github.com/dubuqingfeng/maimai-crawler/models"
	"github.com/dubuqingfeng/maimai-crawler/utils"
	"github.com/json-iterator/go"
	log "github.com/sirupsen/logrus"
	"strconv"
	"strings"
	"time"
)

// 更新细节
type GossipsDetailFetcher struct {
}

func NewGossipsDetailFetcher() GossipsDetailFetcher {
	return GossipsDetailFetcher{}
}

func (g *GossipsDetailFetcher) Fetch(title string) {
	// 首先获取到所有的 gossips
	request := utils.NewRequestGenerator()
	table := "gossips_bitmain"
	gossips := models.GetAllEmptyGossipIdItem(table)
	for _, gossip := range gossips {
		url := fmt.Sprintf("https://maimai.cn/web/gossip_detail?encode_id=%s", gossip.EncodeID)
		body, err := request.Get(url)
		if err != nil {
			log.Error(err)
			continue
		}
		bodyStr := string(body)
		fmt.Println(bodyStr)
		start := strings.Index(bodyStr, "JSON.parse(")
		end := strings.Index(bodyStr, ");</script>")
		if start == -1 || end == -1 {
			time.Sleep(5 * time.Second)
			continue
		}
		json := bodyStr[start+12 : end-1]
		str, err := strconv.Unquote(strings.Replace(strconv.Quote(json), `\\u`, `\u`, -1))
		log.Info(str)
		mmid := jsoniter.Get([]byte(str), "data", "gossip", "mmid").ToString()
		log.Info(mmid)
		models.UpdateGossipItemGossipID(gossip.ID, mmid, table)
		time.Sleep(5 * time.Second)
	}
}
