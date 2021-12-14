package gossip

import (
	"encoding/json"
	"github.com/dubuqingfeng/maimai-crawler/models"
	"github.com/dubuqingfeng/maimai-crawler/utils"
	log "github.com/sirupsen/logrus"
	"github.com/zhshch2002/goribot"
	"strconv"
	"time"
)

type GossipsFetcher struct {
	s     *goribot.Spider
	query string
}

func NewGossipsFetcher() GossipsFetcher {
	s := goribot.NewSpider(
		goribot.Limiter(true, &goribot.LimitRule{
			Glob:  "maimai.cn",
			Rate:  2,
			Delay: 10 * time.Second,
		}),
		goribot.RefererFiller(),
		goribot.SpiderLogPrint(),
		goribot.SetDepthFirst(true),
	)
	query := "比特大陆"
	s.AutoStop = false
	s.SetItemPoolSize(20)
	s.Use(func(s *goribot.Spider) {
		s.OnAdd(func(ctx *goribot.Context, t *goribot.Task) *goribot.Task {
			cookie := utils.Config.Cookie
			t.Request.SetHeader("cookie", cookie)
			ua := "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
			t.Request.SetUA(ua)
			return t
		})
	})
	return GossipsFetcher{s: s, query:query}
}

// 查找职言列表
func (g *GossipsFetcher) FindGossips(ctx *goribot.Context) {
	more := ctx.Resp.Json("data.more").Int()
	gossips := ctx.Resp.Json("data.gossips").Array()
	log.WithField("more", more).Info("len(gossips)", len(gossips))
	if len(gossips) > 0 {
		for _, gossip := range gossips {
			raw := gossip.Get("gossip").Raw
			log.Info(raw)
			var item models.Gossip
			if err := json.Unmarshal([]byte(raw), &item); err != nil {
				log.Error(err)
				continue
			}
			ctx.AddItem(item)
		}
	}
	var isLoadMore bool
	isLoadMore = utils.Config.GossipsIsLoadMore
	if more > 0 && isLoadMore {
		offset, err := utils.GetURLParam(ctx.Resp.Request.URL.String(), "offset")
		if err != nil {
			log.Error(err)
			return
		}
		offsetInt, _ := strconv.Atoi(offset)
		startUrl := "https://maimai.cn/search/gossips"
		g.s.AddTask(goribot.Get(startUrl).AddParam("query", g.query).AddParam("limit", "20").
			AddParam("offset", strconv.Itoa(offsetInt+20)).AddParam("highlight", "true").
			AddParam("sortby", "time").AddParam("jsononly", "1"),
			g.FindGossips)
	}
}

func (g *GossipsFetcher) SaveItem(i interface{}) interface{} {
	item := i.(models.Gossip)
	models.SaveGossipItem("gossips_bitmain", item)
	return i
}

// 抓取职言列表
func (g *GossipsFetcher) Fetch(title string) {
	g.s.OnItem(g.SaveItem)
	startUrl := "https://maimai.cn/search/gossips"
	g.s.AddTask(goribot.Get(startUrl).AddParam("query", g.query).AddParam("limit", "20").
		AddParam("offset", "0").AddParam("highlight", "true").
		AddParam("sortby", "time").AddParam("jsononly", "1"),
		g.FindGossips)
	g.s.Run()
}
