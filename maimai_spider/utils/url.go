package utils

import "net/url"

func GetURLParam(link, param string) (string, error) {
	u, err := url.Parse(link)
	if err != nil {
		return "", err
	}
	for key, value := range u.Query() {
		if key == param {
			return value[0], nil
		}
	}
	return "", nil
}
