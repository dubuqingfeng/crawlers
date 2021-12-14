package utils

import (
	"fmt"
	"github.com/manifoldco/promptui"
)

func PromptSelect(label string, items []string) string {
	prompt := promptui.Select{
		Label: label,
		Items: items,
	}
	_, result, err := prompt.Run()
	if err != nil {
		fmt.Printf("Prompt failed %v\n", err)
		return ""
	}
	return result
}

func PromptInput(label string, validate promptui.ValidateFunc) string {
	prompt := promptui.Prompt{
		Label:    label,
		Validate: validate,
	}

	result, err := prompt.Run()

	if err != nil {
		fmt.Printf("Prompt failed %v\n", err)
		return ""
	}
	return result
}
