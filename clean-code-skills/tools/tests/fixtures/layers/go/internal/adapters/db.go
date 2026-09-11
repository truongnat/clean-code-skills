package adapter

import "github.com/acme/shop/internal/domain"

type Row struct{ ID int }

func Load() domain.Order {
	return domain.Order{}
}
