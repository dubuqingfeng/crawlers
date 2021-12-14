package utils

import (
	"io/ioutil"
	"net/http"
	"time"
)

type RequestGenerator struct {
	client http.Client
}

func NewRequestGenerator() *RequestGenerator {
	client := http.Client{
		Timeout: time.Second * 10,
	}
	return &RequestGenerator{client: client}
}

func (h *RequestGenerator) Get(endpoint string) ([]byte, error) {
	req, err := http.NewRequest("GET", endpoint, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36	")

	res, err := h.client.Do(req)
	if err != nil {
		return nil, err
	}
	body, err := ioutil.ReadAll(res.Body)
	defer res.Body.Close()
	if err != nil {
		return nil, err
	}
	return body, nil
}
