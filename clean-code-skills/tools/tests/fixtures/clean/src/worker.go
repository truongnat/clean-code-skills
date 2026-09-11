package main

import (
	"errors"
	"strings"
)

const maxRetries = 3
const vipCouponPrefix = "VIP"
const vipDiscountPercent = 80
const percentBase = 100

type order struct {
	id     string
	coupon string
	items  []item
}

type item struct {
	price int64
	stock int64
}

func processOrder(repo *Repo, o order) (int64, error) {
	if repo == nil {
		return 0, errors.New("repo is required")
	}
	total, err := sumSellable(o.items)
	if err != nil {
		return 0, err
	}
	return applyCoupon(total, o.coupon), nil
}

func sumSellable(items []item) (int64, error) {
	var total int64
	for _, it := range items {
		if !isSellable(it) {
			continue
		}
		total += it.price
	}
	return total, nil
}

func isSellable(it item) bool {
	return it.price > 0 && it.stock > 0
}

func applyCoupon(total int64, coupon string) int64 {
	if !strings.HasPrefix(coupon, vipCouponPrefix) {
		return total
	}
	return total * vipDiscountPercent / percentBase
}

func retryable(attempt int) bool {
	return attempt < maxRetries
}
