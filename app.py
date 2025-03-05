import pandas as pd
import streamlit as st
import io
import re

def match_skus_and_extract_info(amazon_sale_order_template, cp_item_list, product_bundle):
    """
    Match Amazon SKUs from the Amazon Sale Order Template with CP Item List.
    Use CP Item List to connect to the Product Bundle for Parent Item Code and Bundle Quantity.
    """

    output_rows = []

    for _, order_row in amazon_sale_order_template.iterrows():
        amazon_sku = order_row['asin']
        total_amount = order_row['item-price']

        # Match ASIN with CP Item List
        matched_cp_item = cp_item_list[cp_item_list['Amazon ASIN'] == amazon_sku]

        if not matched_cp_item.empty:766654
            item_code = matched_cp_item.iloc[0]['Item Code']

            # Find matching Product Bundle details using Item Code
            matched_bundle = product_bundle[product_bundle['ID'] == item_code]

            if not matched_bundle.empty:
                parent_item_code = matched_bundle.iloc[0]['ID']
                total_quantity = int(matched_bundle.iloc[0]['Qty (Product Bundle Item)'])

                # Regex to find "Pack of X"
                match = re.search(r'\(Pack of (\d+)\)', matched_bundle.iloc[0]['ID'])
                bundle_quantity = int(match.group(1)) if match else 1  # Default to 1 if no match
    

                price_per_packet = total_amount * bundle_quantity/ total_quantity if total_quantity else 0

                state = str(order_row.get('ship-state', '')).strip()
                state = state.title() if state else "Unknown"
                customer = f"Amazon Customer ({state})"

                output_rows.append({
                    'Item Code (Items)': parent_item_code,
                    'Quantity (Items)': total_quantity,
                    'Rate (Items)': price_per_packet,
                    'Customer': customer, 
                })

    output_df = pd.DataFrame(output_rows)
    return output_df

def modify_template(amazon_sale_order_template_file, cp_item_list_file, product_bundle_file):
    """
    Process files and return the final output DataFrame.
    """
    amazon_sale_order_template = pd.read_excel(amazon_sale_order_template_file)
    cp_item_list = pd.read_excel(cp_item_list_file)
    product_bundle = pd.read_excel(product_bundle_file)

    output_df = match_skus_and_extract_info(
        amazon_sale_order_template,
        cp_item_list,
        product_bundle
    )

    output_df['Company'] = ''  # Formula
    output_df['Cost Center'] = '6 - Retail - TMPL'
    output_df['Currency'] = 'INR'
    output_df['Date'] = amazon_sale_order_template['purchase-date']
    output_df['Order Type'] = 'Shopping Cart'
    output_df['Price List'] = 'Standard Selling'
    output_df['Price List Currency'] = 'INR'
    output_df['Series'] = 'SAL-ORD-.YYYY.-'
    output_df['Company Address'] = ''  # Formula
    output_df['Company Address Name'] = ''
    output_df['Customer\'s Purchase Order'] = amazon_sale_order_template['amazon-order-id']
    output_df['Customer\'s Purchase Order Date'] = amazon_sale_order_template['purchase-date']
    output_df['Payment Terms Template'] = '7DINVOICE_LOCAL'
    output_df['Sales Taxes and Charges Template'] = ''
    output_df['Set Source Warehouse'] = ''
    output_df['UOM (Items)'] = 'Nos'
    output_df['Delivery Date (Items)'] = ''
    output_df['Delivery Warehouse (Items)'] = ''
    output_df['Rate of Stock UOM (Items)'] = ''  # formula
    

    return output_df

def main():
    st.title("Amazon Order Processor")

    amazon_sale_order_template_file = st.file_uploader("Upload Amazon Sale Order Template", type=["xlsx", "xls"])
    cp_item_list_file = st.file_uploader("Upload CP Item List", type=["xlsx", "xls"])
    product_bundle_file = st.file_uploader("Upload Product Bundle File", type=["xlsx", "xls"])

    if amazon_sale_order_template_file and cp_item_list_file and product_bundle_file:
        output_df = modify_template(
            amazon_sale_order_template_file,
            cp_item_list_file,
            product_bundle_file
        )

        st.write("Processed Data:")
        st.dataframe(output_df)

        output_buffer = io.BytesIO()
        output_df.to_excel(output_buffer, index=False)
        output_buffer.seek(0)

        st.download_button(
            label="Download Processed Excel File",
            data=output_buffer,
            file_name="processed_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
