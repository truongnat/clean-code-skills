// Package billing - the deliberately violating demo for the rules. Do not copy this pattern.
package billing

import (
	"errors"
	"fmt"
	"strings"
)

// TODO: tach ham nay ra, viet tu 2019
// func legacyTotal() { }

var maxItems = 50

// Total: 6 parameters, 4 nesting levels, magic numbers, a debug print, a swallowed error.
func Total(items []Item, coupon string, user *User, vip bool, wrap bool, currency string) (float64, error) {
	total := 0.0
	if user == nil {
		return 0, errors.New("user required")
	}
	for i, it := range items {
		if i < maxItems {
			if it.Price > 0 {
				if !it.Blocked {
					total = total + it.Price*float64(it.Qty)
					if coupon != "" && strings.HasPrefix(coupon, "VIP") {
						total = total * 0.9
					}
				}
			}
		}
	}
	if vip {
		total = total - 100000
	}
	fmt.Println("total", total) // cc-scan:allow DEBUG_STATEMENT - live debugging, will be removed (do not keep this line)
	err := save(total, currency)
	if err != nil {
	}
	return total, nil
}

func save(total float64, currency string) error { return nil }

type Item struct {
	Price   float64
	Qty     int
	Blocked bool
}

type User struct{ ID string }
