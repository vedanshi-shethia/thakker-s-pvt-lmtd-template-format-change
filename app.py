import streamlit as st
import io
import pandas as pd
from helpers.order_processor import OrderProcessor


def main():
    st.title("Amazon Order Processor")

    amazon_file = st.file_uploader("Upload Amazon Sale Order Template", type=["xlsx", "xls"])
    cp_file = st.file_uploader("Upload CP Item List", type=["xlsx", "xls"])
    product_bundle_file = st.file_uploader("Upload Product Bundle File", type=["xlsx", "xls"])

    if amazon_file and cp_file and product_bundle_file:
        processor = OrderProcessor(amazon_file, cp_file, product_bundle_file)
        output_df = processor.process()

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
