import pandas as pd
from datetime import datetime
from helpers.utils import extract_pack_of_quantity, calculate_price_per_packet, format_state
from helpers.file_handler import FileHandler

class SaleOrderTemplate:

    REQUIRED_AMAZON_COLUMNS = ['asin', 'item-price', 'quantity', 'ship-state', 'purchase-date', 'amazon-order-id']
    REQUIRED_CP_COLUMNS = ['Amazon ASIN', 'Item Code']
    REQUIRED_BUNDLE_COLUMNS = ['ID', 'Item (Product Bundle Item)', 'Qty (Product Bundle Item)']
    
    def __init__(self, amazon_file, cp_file, product_bundle_file):
        self.amazon_df = FileHandler.read_excel(amazon_file)
        self.cp_df = FileHandler.read_excel(cp_file)
        self.bundle_df = FileHandler.read_excel(product_bundle_file)

        FileHandler.validate_columns(self.amazon_df, self.REQUIRED_AMAZON_COLUMNS, "Amazon Sale Order Template")
        FileHandler.validate_columns(self.cp_df, self.REQUIRED_CP_COLUMNS, "CP Item List")
        FileHandler.validate_columns(self.bundle_df, self.REQUIRED_BUNDLE_COLUMNS, "Product Bundle")

    def process(self):
        output_rows = []
        error_rows = []

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

            state = format_state(order.get('ship-state'))
            customer = f"Amazon Sales ({state})"

            date_obj = datetime.fromisoformat(order['purchase-date'])
            formatted_date = date_obj.strftime("%Y-%m-%d")

            cp_match = self.cp_df[self.cp_df['Amazon ASIN'] == asin]
            if cp_match.empty:
                item_code_error_message = f"Error: No CP Item for ASIN {asin}"

                error_rows.append({
                    'Item Code (Items)': item_code_error_message,
                    'Customer': customer,
                    'Date': formatted_date,
                    'Customer\'s Purchase Order': order['amazon-order-id'],
                    'Customer\'s Purchase Order Date': formatted_date,
                    'Rate of Stock UOM (Items)': str(price_per_packet),
                    'Fulfilled By': order['fulfillment-channel']
                })

            else:
                item_code = cp_match.iloc[0]['Item Code']
                bundle_match = self.bundle_df[self.bundle_df['ID'] == item_code]
                if bundle_match.empty:
                    item_code_error_message = f"Error: No Product Bundle for Item Code {item_code}"

                    error_rows.append({
                        'Item Code (Items)': item_code_error_message,
                        'Customer': customer,
                        'Date': formatted_date,
                        'Customer\'s Purchase Order': order['amazon-order-id'],
                        'Customer\'s Purchase Order Date': formatted_date,
                        'Rate of Stock UOM (Items)': str(price_per_packet),
                        'Fulfilled By': order['fulfillment-channel']
                    })

                else:
                    item_code = bundle_match.iloc[0]['Item (Product Bundle Item)']
                    product_bundle_quantity = int(bundle_match.iloc[0]['Qty (Product Bundle Item)'])

                    if(not product_bundle_quantity or not amazon_quantity or not bundle_quantity):

                        error_message = f"Error while calculating rate"

                        error_rows.append({
                            'Item Code (Items)': str(item_code),
                            'Rate (Items)': error_message,
                            'Customer': customer,
                            'Date': formatted_date,
                            'Customer\'s Purchase Order': order['amazon-order-id'],
                            'Customer\'s Purchase Order Date': formatted_date,
                            'Rate of Stock UOM (Items)': error_message,
                            'Fulfilled By': order['fulfillment-channel']
                        })

                    else :
                        price_per_packet = calculate_price_per_packet(
                            item_price, product_bundle_quantity, amazon_quantity
                        )

                        output_rows.append({
                            'Item Code (Items)': str(item_code),
                            'Quantity (Items)': str(product_bundle_quantity * amazon_quantity),
                            'Rate (Items)': str(price_per_packet),
                            'Customer': customer,
                            'Date': formatted_date,
                            'Customer\'s Purchase Order': order['amazon-order-id'],
                            'Customer\'s Purchase Order Date': formatted_date,
                            'Rate of Stock UOM (Items)': str(price_per_packet),
                            'Fulfilled By': order['fulfillment-channel']
                        })

        output_df = pd.DataFrame(output_rows)
        error_rows = pd.DataFrame(error_rows)
        return [self.add_default_columns(output_df), self.add_default_columns(error_rows)]



    def add_default_columns(self, df):
        df['Company'] = ''
        df['Cost Center'] = '6 - Retail - TMPL'
        df['Currency'] = 'INR'
        df['Order Type'] = 'Shopping Cart'
        df['Price List'] = 'Standard Selling'
        df['Status'] = 'Draft'
        df['Price List Exchange Rate'] = '1'
        df['Exchange Rate'] = '1'
        df['Cost Center (Items)'] = '6 - Retail - TMPL'
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