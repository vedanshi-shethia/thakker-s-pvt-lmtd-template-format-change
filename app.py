import pandas as pd
import streamlit as st
import io

def modify_template(sheet1_file):
    # Read the uploaded file
    sheet1 = pd.read_excel(sheet1_file)
    
    # Create an empty dataframe for the output
    output_df = pd.DataFrame()

    # Modify output DataFrame based on your logic
    output_df['Company'] = ''  # Formula
    output_df['Cost Center'] = '6 - Retail - TMPL'
    output_df['Currency'] = 'INR'
    output_df['Date'] = sheet1['purchase-date']
    output_df['Order Type'] = 'Shopping Cart'
    output_df['Price List'] = 'Standard Selling'
    output_df['Price List Currency'] = 'INR'
    output_df['Series'] = 'SAL-ORD-.YYYY.-'
    output_df['Company Address'] = ''  # Formula
    output_df['Company Address Name'] = ''
    output_df['Customer\'s Purchase Order'] = sheet1['amazon-order-id']
    output_df['Customer\'s Purchase Order Date'] = sheet1['purchase-date']
    output_df['Payment Terms Template'] = '7DINVOICE_LOCAL'
    output_df['Sales Taxes and Charges Template'] = ''
    output_df['Set Source Warehouse'] = ''
    output_df['Item Code (Items)'] = ''  # formula
    output_df['Quantity (Items)'] = ''  # formula
    output_df['UOM (Items)'] = 'Nos'
    output_df['Delivery Date (Items)'] = ''
    output_df['Delivery Warehouse (Items)'] = ''
    output_df['Rate (Items)'] = ''  # formula
    output_df['Rate of Stock UOM (Items)'] = ''  # formula
    
    return output_df

def main():
    st.title("Excel File Processor")
    
    # File upload widget for Sheet1
    sheet1_file = st.file_uploader("Upload Amazon Excel File", type=["xlsx", "xls"])
    
    if sheet1_file:
        # Process the file if uploaded
        output_df = modify_template(sheet1_file)
        
        # Display the processed data in the app
        st.write("Processed Data:")
        st.dataframe(output_df)
        
        # Save the dataframe to a BytesIO buffer
        output_buffer = io.BytesIO()
        output_df.to_excel(output_buffer, index=False)
        output_buffer.seek(0)  # Reset the buffer position to the beginning

        # Allow user to download the processed Excel file
        st.download_button(
            label="Download Processed Excel File",
            data=output_buffer,
            file_name="output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
