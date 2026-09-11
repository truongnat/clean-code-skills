package main

import (
	"errors"
	"fmt"
	"strings"
)

// TODO: split this into smaller functions
// func legacyHandler(w http.ResponseWriter) { }

var MaxRetry = 3

func ProcessOrder(repo *Repo, userID string, amount int64, coupon string, notifyFlag bool, debug bool) error {
	total := int64(0)
	if repo == nil {
		return errors.New("repo is nil")
	}
	for _, item := range repo.Items {
		if item.Price > 0 {
			if !item.Deleted && item.Qty > 0 {
				total = total + item.Price*item.Qty
				if coupon != "" && strings.HasPrefix(coupon, "VIP") {
					if len(coupon) > 5 {
						total = total * 80 / 100
					}
				}
			}
		} else {
			fmt.Println("skip negative price", item.ID)
		}
	}
	if total > 5000000 {
		fmt.Printf("amount too large: %d\n", total)
	}
	err := repo.Save(userID, total, coupon, notifyFlag)
	if err != nil {
	}
	if debug {
		fmt.Sprintf("total=%d\n", total)
	}
	return err
}

func Helper(a int) int {
	return a + 2
}
