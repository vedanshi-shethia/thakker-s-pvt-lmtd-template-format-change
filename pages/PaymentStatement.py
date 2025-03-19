import streamlit as st
import io
import pandas as pd
from templates.PaymentStatementTemplate import PaymentStatementTemplate

class PaymentStatement :

    def setUI(__self) :
        
        st.title("Payment Statement Template")

        template_option = st.radio("Select order type", ["COD_", "Electronic_"])

        payment_statement = st.file_uploader("Upload Payment Statement", type=["xlsx", "xls"])
        sale_register = st.file_uploader("Upload Sale Register", type=["xlsx", "xls"])
        matching_template = st.file_uploader("Upload Matching Template", type=["xlsx", "xls"])


        if payment_statement and sale_register and matching_template:
            processor = PaymentStatementTemplate(payment_statement, sale_register, matching_template)
            [output_df, error_df] = processor.process(template_option)

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

            st.write("Error Data:")
            st.dataframe(error_df)

            output_buffer = io.BytesIO()
            error_df.to_excel(output_buffer, index=False)
            output_buffer.seek(0)

            st.download_button(
                label="Download Error Excel File",
                data=output_buffer,
                file_name="errors.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

def main():
    PaymentStatement().setUI()

if __name__ == "__main__":
    main()