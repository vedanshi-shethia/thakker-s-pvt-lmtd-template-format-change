import pandas as pd
from datetime import datetime
from .utils import extract_pack_of_quantity, calculate_price_per_packet, format_state
from .file_handler import FileHandler

class OrderProcessor:

    def __init__(self, amazon_file, cp_file, product_bundle_file):
        self.amazon_df = FileHandler.read_excel(amazon_file)
        self.cp_df = FileHandler.read_excel(cp_file)
        self.bundle_df = FileHandler.read_excel(product_bundle_file)

        FileHandler.validate_columns(self.amazon_df, ['asin', 'item-price', 'quantity', 'ship-state', 'purchase-date', 'amazon-order-id'], "Amazon Sale Order Template")
        FileHandler.validate_columns(self.cp_df, ['Amazon ASIN', 'Item Code'], "CP Item List")
        FileHandler.validate_columns(self.bundle_df, ['ID', 'Item (Product Bundle Item)', 'Qty (Product Bundle Item)'], "Product Bundle")

    def process(self):
        output_rows = []

        for _, order in self.amazon_df.iterrows():
            asin = order['asin']
            item_price = order['item-price']
            amazon_quantity = int(order['quantity'])

            # Defaults
            item_code = ''
            product_bundle_quantity = ''
            bundle_quantity = 1
            price_per_packet = ''
            error_text = ''

            cp_match = self.cp_df[self.cp_df['Amazon ASIN'] == asin]
            if cp_match.empty:
                item_code = f"Error: No CP Item for ASIN {asin}"
                product_bundle_quantity = f"Error: No CP Item"
                price_per_packet = f"Error: No CP Item"
            else:
                item_code = cp_match.iloc[0]['Item Code']
                bundle_match = self.bundle_df[self.bundle_df['ID'] == item_code]
                if bundle_match.empty:
                    item_code = f"Error: No Product Bundle for Item Code {item_code}"
                    product_bundle_quantity = f"Error: No Bundle"
                    price_per_packet = f"Error: No Bundle"
                else:
                    item_code = bundle_match.iloc[0]['Item (Product Bundle Item)']
                    product_bundle_quantity = int(bundle_match.iloc[0]['Qty (Product Bundle Item)'])
                    bundle_quantity = extract_pack_of_quantity(bundle_match.iloc[0]['ID'])

                    price_per_packet = calculate_price_per_packet(
                        item_price, bundle_quantity, product_bundle_quantity, amazon_quantity
                    )

            state = format_state(order.get('ship-state'))
            customer = f"Amazon Customer ({state})"

            date_obj = datetime.fromisoformat(order['purchase-date'])
            formatted_date = date_obj.strftime("%Y-%m-%d")

            output_rows.append({
                'Item Code (Items)': str(item_code),
                'Quantity (Items)': str(product_bundle_quantity),
                'Rate (Items)': str(price_per_packet),
                'Customer': customer,
                'Date': formatted_date,
                'Customer\'s Purchase Order': order['amazon-order-id'],
                'Customer\'s Purchase Order Date': formatted_date,
                'Rate of Stock UOM (Items)': str(price_per_packet),
                'FulFilled': order['fulfillment-channel']
            })

        output_df = pd.DataFrame(output_rows)
        return self.add_default_columns(output_df)



    def add_default_columns(self, df):
        df['Company'] = ''
        df['Cost Center'] = '6 - Retail - TMPL'
        df['Currency'] = 'INR'
        df['Order Type'] = 'Shopping Cart'
        df['Price List'] = 'Standard Selling'
        df['Price List Currency'] = 'INR'
        df['Series'] = 'SAL-ORD-.YYYY.-'
        df['Company Address'] = ''
        df['Company Address Name'] = ''
        df['Payment Terms Template'] = '7DINVOICE_LOCAL'
        df['Sales Taxes and Charges Template'] = ''
        df['Set Source Warehouse'] = ''
        df['UOM (Items)'] = 'Nos'
        df['Delivery Date (Items)'] = ''
        df['Delivery Warehouse (Items)'] = ''
        return df
