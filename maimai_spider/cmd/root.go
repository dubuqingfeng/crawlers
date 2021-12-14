package cmd

import (
	"github.com/dubuqingfeng/maimai-crawler/fetchers/gossip"
	"github.com/dubuqingfeng/maimai-crawler/utils"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"time"
)

var (
	rootCmd = &cobra.Command{
		Use:   "maimai",
		Short: "maimai CLI",
		Run:   run,
	}
	cfgFile  string
	commands = []string{"爬取职言列表", "更新职言列表状态", "爬取职言评论"}
)

// initConfig reads in config file.
func initConfig() {
	if cfgFile != "" {
		err := utils.InitConfig(cfgFile)
		if err != nil {
			log.Error(err)
		}
		// 设置 MySQL
		utils.SetMySQLConfigs()
	}
}

func init() {
	initLog()
	cobra.OnInitialize(initConfig)
	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "./configs/config.yaml",
		"config file (default is configs/config.yaml)")
	rootCmd.AddCommand()
}

func initLog() {
	level, err := log.ParseLevel("debug")
	if err != nil {
		level = log.DebugLevel
	}
	log.SetLevel(level)
	log.SetFormatter(&log.JSONFormatter{TimestampFormat: "2006-01-02 15:04:05.000"})
	utils.ConfigLocalFileSystemLogger("./logs", "/maimai.log")
	utils.ConfigRotateLocalFileSystemLogger("./logs", "maimai.log",
		7*time.Hour*24, time.Second*20)
}

// execute
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		log.Panic(err)
	}
}

func run(cmd *cobra.Command, args []string) {
	result := utils.PromptSelect("进行您的选择", commands)
	switch result {
	case "爬取职言列表":
		fetcher := gossip.NewGossipsFetcher()
		fetcher.Fetch("test")
		break
	case "更新职言列表状态":
		fetcher := gossip.NewGossipsDetailFetcher()
		fetcher.Fetch("test")
		break
	case "爬取职言评论":
		fetcher := gossip.NewCommentsFetcher()
		fetcher.Fetch("test")
		break
	}
}
