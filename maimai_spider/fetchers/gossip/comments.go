package gossip

import (
	"encoding/json"
	"fmt"
	"github.com/dubuqingfeng/maimai-crawler/models"
	"github.com/dubuqingfeng/maimai-crawler/utils"
	log "github.com/sirupsen/logrus"
	"github.com/zhshch2002/goribot"
	"strconv"
	"time"
)

type CommentsFetcher struct {
	s *goribot.Spider
}

func NewCommentsFetcher() CommentsFetcher {
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
	s.AutoStop = false
	s.SetItemPoolSize(50)
	s.Use(func(s *goribot.Spider) {
		s.OnAdd(func(ctx *goribot.Context, t *goribot.Task) *goribot.Task {
			cookie := utils.Config.Cookie
			t.Request.SetHeader("cookie", cookie)
			ua := "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
			t.Request.SetUA(ua)
			return t
		})
	})
	return CommentsFetcher{s: s}
}

func (g *CommentsFetcher) SaveItem(i interface{}) interface{} {
	log.Info(i)
	item := i.(models.GossipComment)
	models.SaveCommentItem("gossip_comments_bitmain", item)
	return i
}

// 查找职言列表
func (g *CommentsFetcher) FindGossipComments(ctx *goribot.Context) {
	more := ctx.Resp.Json("more").Int()
	fmt.Println(ctx.Resp.Request.URL.String())
	fmt.Println(ctx.Resp.Json("comments").Raw)
	comments := ctx.Resp.Json("comments").Array()
	gid := ctx.Req.Meta["gid"].(string)
	egid := ctx.Req.Meta["egid"].(string)
	log.WithField("more", more).Info("len(comments)", len(comments))
	if len(comments) > 0 {
		for _, comment := range comments {
			raw := comment.Raw
			log.Info(raw)
			var item models.GossipComment
			if err := json.Unmarshal([]byte(raw), &item); err != nil {
				log.Error(err)
				continue
			}
			item.GossipId, _ = strconv.Atoi(gid)
			ctx.AddItem(item)
		}
	}
	var isLoadMore bool
	isLoadMore = true
	if more > 0 && isLoadMore {
		// offset, err := utils.GetURLParam(ctx.Resp.Request.URL.String(), "offset")
		page, err := utils.GetURLParam(ctx.Resp.Request.URL.String(), "page")
		if err != nil {
			log.Error(err)
			return
		}
		pageInt, _ := strconv.Atoi(page)
		// offsetInt, _ := strconv.Atoi(page)
		log.Info(pageInt)
		startUrl := "https://maimai.cn/sdk/web/gossip/getcmts"
		u := utils.Config.Auth.U
		csrf := utils.Config.Auth.CSRF
		csrfToken := utils.Config.Auth.CSRFToken
		accessToken := utils.Config.Auth.AccessToken
		g.s.AddTask(goribot.Get(startUrl).WithMeta("gid", gid).WithMeta("egid", egid).
			AddParam("gid", gid).AddParam("egid", egid).
			AddParam("page", strconv.Itoa(pageInt + 1)).AddParam("count", "405").
			AddParam("hotcmts_limit_count", "1").AddParam("u", u).
			AddParam("channel", "www").AddParam("version", "4.0.0").
			AddParam("_csrf", csrf).AddParam("_csrf_token", csrfToken).AddParam("access_token", accessToken),
			g.FindGossipComments)
	}
}

func (g *CommentsFetcher) Fetch(title string) {
	g.s.OnItem(g.SaveItem)
	startUrl := "https://maimai.cn/sdk/web/gossip/getcmts"
	u := utils.Config.Auth.U
	csrf := utils.Config.Auth.CSRF
	csrfToken := utils.Config.Auth.CSRFToken
	accessToken := utils.Config.Auth.AccessToken
	// 获取职言 id
	gossips := models.GetCrawlCommentsGossipItems("gossips_bitmain")
	for _, gossip := range gossips {
		gid := gossip.ID
		egid := gossip.Egid
		g.s.AddTask(goribot.Get(startUrl).WithMeta("gid", gid).WithMeta("egid", egid).
			AddParam("gid", gid).AddParam("egid", egid).
			AddParam("page", "0").AddParam("count", "405").
			AddParam("hotcmts_limit_count", "1").AddParam("u", u).
			AddParam("channel", "www").AddParam("version", "4.0.0").
			AddParam("_csrf", csrf).AddParam("_csrf_token", csrfToken).AddParam("access_token", accessToken),
			g.FindGossipComments)
	}
	g.s.Run()
}
