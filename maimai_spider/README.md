## 脉脉爬虫

### 过程

1. 运行职言区爬虫

go run main.go


2. 更新职言列表状态

更新职言列表状态、

抓取更新职言 ID

3. 抓取职言列表评论


### Q&A

1. 获取 ua

https://httpbin.org/get



### SQL

```sql

select a.id, a.crtime, a.total_cnt, a.gossip_status,ifnull(b.count, 0) from gossips a left join 
(select gossip_id, count(*) as count from gossip_comments group by gossip_id) b
on a.id=b.gossip_id order by a.id;

select gossips.id, gossip_comments.mmid, gossip_comments.text, gossips.crtime from gossip_comments left join gossips on gossips.id = gossip_comments.gossip_id order by mmid, gossips.crtime;

```