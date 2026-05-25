REQUIRED_PAYMENT_COLUMNS = {
        "settlement-start-date",
        "settlement-end-date",
        "order-id",
        "amount",
        "posted-date",
        "amount-description",
        "amount-type",
    }

REQUIRED_SALE_REGISTER_COLUMNS = {
    "Customer's Purchase Order",
    "Company GSTIN",
    "Customer Name",
    "Voucher",
    "Voucher Type",
    "Posting Date",
    "Cost Center",
    "Company",
}

REQUIRED_MATCHING_TEMPLATE_COLUMNS = {
    "amount-description",
    "ERP 27 Company",
    "ERP 29 Company",
}

REQUIRED_AMAZON_COLUMNS = ['asin', 'item-price', 'quantity', 'ship-state', 'purchase-date', 'amazon-order-id']

REQUIRED_CP_COLUMNS = ['Amazon ASIN', 'Item Code']

REQUIRED_BUNDLE_COLUMNS = ['ID', 'Item (Product Bundle Item)', 'Qty (Product Bundle Item)']