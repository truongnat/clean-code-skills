// Package billing: order pricing, pure logic kept apart from I/O so tests need no database.
package billing

import (
	"errors"
	"strings"
)

// ErrNoUser is returned when the order is not attached to any user.
var ErrNoUser = errors.New("billing: user is required")

const (
	vipCouponPrefix  = "VIP"
	vipRate          = 0.9
	minCouponLength  = 3
	defaultItemLimit = 50
)

// Item is one line of an order.
type Item struct {
	Price   float64
	Qty     int
	Blocked bool
}

// Sellable filters the billable lines without mutating the input.
func Sellable(items []Item, limit int) []Item {
	considered := min(len(items), limit)
	out := make([]Item, 0, considered)
	for _, it := range items[:considered] {
		if isChargeable(it) {
			out = append(out, it)
		}
	}
	return out
}

func isChargeable(it Item) bool {
	return it.Price > 0 && !it.Blocked
}

// Subtotal sums the valid lines.
func Subtotal(items []Item) float64 {
	var total float64
	for _, it := range items {
		total += it.Price * float64(it.Qty)
	}
	return total
}

// ApplyVip discounts when the coupon is long enough and starts with VIP.
func ApplyVip(subtotal float64, coupon string) float64 {
	if len(coupon) < minCouponLength || !strings.HasPrefix(coupon, vipCouponPrefix) {
		return subtotal
	}
	return subtotal * vipRate
}

// Total composes the steps: filter -> sum -> discount. Returned errors carry context.
func Total(items []Item, coupon string) (float64, error) {
	if len(items) == 0 {
		return 0, errors.Join(ErrNoUser, errors.New("cart is empty"))
	}
	sub := Subtotal(Sellable(items, defaultItemLimit))
	return ApplyVip(sub, coupon), nil
}
