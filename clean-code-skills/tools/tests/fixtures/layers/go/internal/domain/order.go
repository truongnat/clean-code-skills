package domain

import (
	"fmt"
	"database/sql" // driver in the domain

	"github.com/acme/shop/internal/adapters"
)

type Order struct{ total int }

func (o Order) String() string {
	return fmt.Sprint(o.total, adapter.Row{})
}
