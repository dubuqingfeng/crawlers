package utils

import (
	"github.com/lestrrat-go/file-rotatelogs"
	"github.com/pkg/errors"
	"github.com/rifflock/lfshook"
	log "github.com/sirupsen/logrus"
	"os"
	"path"
	"time"
)

func ConfigLocalFileSystemLogger(logPath string, logFileName string) {
	mod := os.O_CREATE | os.O_APPEND | os.O_WRONLY
	if file, err := os.OpenFile(logPath+logFileName, mod, 0644); err == nil {
		log.SetOutput(file)
	} else {
		panic(err)
	}
}

// Rotate Log
func ConfigRotateLocalFileSystemLogger(logPath string, logFileName string, maxAge time.Duration, rotationTime time.Duration) {
	baseLogPath := path.Join(logPath, logFileName)
	writer, err := rotatelogs.New(
		baseLogPath+".%Y%m%d",
		//rotatelogs.WithLinkName(baseLogPath),
		rotatelogs.WithMaxAge(maxAge),
		rotatelogs.WithRotationTime(rotationTime),
	)

	if err != nil {
		log.Errorf("config local file system logger error. %+v", errors.WithStack(err))
	}

	lfHook := lfshook.NewHook(lfshook.WriterMap{
		log.DebugLevel: writer,
		log.InfoLevel:  writer,
		log.WarnLevel:  writer,
		log.ErrorLevel: writer,
		log.FatalLevel: writer,
		log.PanicLevel: writer,
	}, &log.JSONFormatter{TimestampFormat: "2006-01-02 15:04:05.000"})
	log.AddHook(lfHook)
}
