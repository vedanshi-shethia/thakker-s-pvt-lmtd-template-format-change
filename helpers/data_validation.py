import pandas as pd
from datetime import datetime
from helpers.required_columns import REQUIRED_MATCHING_TEMPLATE_COLUMNS, REQUIRED_PAYMENT_COLUMNS, REQUIRED_SALE_REGISTER_COLUMNS, REQUIRED_AMAZON_COLUMNS, REQUIRED_CP_COLUMNS, REQUIRED_BUNDLE_COLUMNS
class DataValidator:
    @staticmethod
    def is_null(value) -> bool:
        """Returns True if the value is missing or an empty string."""
        return pd.isna(value) or str(value).strip() == ""

    @staticmethod
    def is_valid_date(value, expected_format: str) -> bool:
        """Returns True if the value matches the expected datetime format string."""
        if DataValidator.is_null(value):
            return False
        try:
            datetime.strptime(str(value).strip(), expected_format)
            return True
        except ValueError:
            return False
        
    @staticmethod
    def is_valid_iso_date(value) -> bool:
        """Returns True if the value can be successfully parsed as an ISO format date."""
        if DataValidator.is_null(value):
            return False
        try:
            datetime.fromisoformat(str(value).strip())
            return True
        except ValueError:
            return False

    @staticmethod
    def is_numeric(value) -> bool:
        """Returns True if the value can safely be evaluated as a float/integer."""
        if DataValidator.is_null(value):
            return False
        try:
            float(value)
            return True
        except ValueError:
            return False

    @classmethod
    def validate_payment_statement(cls, df: pd.DataFrame) -> list:
        """
        Validates all columns in REQUIRED_PAYMENT_COLUMNS for the Payment Statement.
        Covers: settlement-start-date, settlement-end-date, order-id, amount, 
                posted-date, amount-description, amount-type
        """
        errors = []
        
        if df.empty:
            return ["Payment Statement file is completely empty."]

        # Expected target date formats
        header_date_format = "%d.%m.%Y %H:%M:%S %Z"  # e.g., 13.04.2026 16:17:47 UTC
        transaction_date_format = "%d.%m.%Y"         # e.g., 16.04.2026

        # ---------------------------------------------------------------------
        # 1. Validation for Row 1 (Index 0) - Global Settlement Summary Header Row
        # ---------------------------------------------------------------------
        header_row = df.iloc[0]
        row_num_1 = 1  # 1-based representation matching Excel UI rows
        
        # Validate 'settlement-start-date'
        start_date = header_row.get("settlement-start-date")
        if cls.is_null(start_date):
            errors.append(f"Row {row_num_1}: Column 'settlement-start-date' is missing or null in the summary header row.")
        elif not cls.is_valid_date(start_date, header_date_format):
            errors.append(f"Row {row_num_1}: Column 'settlement-start-date' has an invalid date format or value '{start_date}'. Expected format: 'DD.MM.YYYY HH:MM:SS TZ' (e.g., '13.04.2026 16:17:47 UTC').")

        # Validate 'settlement-end-date'
        end_date = header_row.get("settlement-end-date")
        if cls.is_null(end_date):
            errors.append(f"Row {row_num_1}: Column 'settlement-end-date' is missing or null in the summary header row.")
        elif not cls.is_valid_date(end_date, header_date_format):
            errors.append(f"Row {row_num_1}: Column 'settlement-end-date' has an invalid date format or value '{end_date}'. Expected format: 'DD.MM.YYYY HH:MM:SS TZ'.")

        # ---------------------------------------------------------------------
        # 2. Validation for Row 2 Onwards (Index 1+) - Individual Transaction Rows
        # ---------------------------------------------------------------------
        # Using df.iloc[:-1] skips the very last row (the total row)
        for index, row in df.iloc[1:-1].iterrows():
            row_num = index + 1  # 1-based representation matching Excel UI rows
            
            posted_date = row.get("posted-date")
            amount = row.get("amount")

            # 1. Presence Checks for All Required Columns
            for col in ["posted-date", "amount-description", "amount-type", "amount"]:
                if cls.is_null(row.get(col)):
                    errors.append(f"Row {row_num}: Required column '{col}' is missing in Payment Statement.")

            # 2. Format Validation: Amount
            if not cls.is_null(amount) and not cls.is_numeric(amount):
                errors.append(f"Row {row_num}: Column 'amount' has a non-numeric value '{amount}'.")

            # 3. Format Validation: Posted Date
            if cls.is_null(posted_date):
                errors.append(f"Row {row_num}: Column 'posted-date' is missing or null.")
            elif not cls.is_valid_date(posted_date, transaction_date_format):
                errors.append(f"Row {row_num}: Column 'posted-date' has an invalid date format or value '{posted_date}'. Expected format: 'DD.MM.YYYY' (e.g., '16.04.2026').")

        return errors
    
    @classmethod
    def validate_sale_register(cls, df: pd.DataFrame) -> list:
        """
        Validates all critical data columns inside the Sale Register file.
        Covers: Customer's Purchase Order, Company GSTIN, Customer Name, 
                Voucher, Voucher Type, Posting Date, Cost Center, Company
        """
        errors = []

        if df.empty:
            return ["Sale Register file is completely empty."]

        # Target date format expected for Sale Register (e.g., '05-04-2026')
        sale_register_date_format = "%d-%m-%Y"

        # Using df.iloc[:-1] skips the very last row (the total row)
        for index, row in df.iloc[:-1].iterrows():
            row_num = index + 1  # 1-based excel sheet representation

            # 1. Presence Checks for All Required Columns
            required_cols = {
                "Company GSTIN",
                "Customer Name",
                "Voucher",
                "Voucher Type",
                "Posting Date",
                "Cost Center",
                "Company",
            }
            
            for col in required_cols:
                if cls.is_null(row.get(col)):
                    errors.append(f"Row {row_num}: Required column '{col}' is missing or null in Sale Register.")

            # 2. Format Validation: Posting Date
            posting_date = row.get("Posting Date")
            if not cls.is_null(posting_date) and not cls.is_valid_date(posting_date, sale_register_date_format):
                errors.append(
                    f"Row {row_num}: Column 'Posting Date' has an invalid date format or value '{posting_date}'. "
                    f"Expected format: 'DD-MM-YYYY' (e.g., '25-04-2026')."
                )
                
        return errors

    
    @classmethod
    def validate_amazon_sale_order_template(cls, df: pd.DataFrame) -> list:
        """
        Validates columns in REQUIRED_AMAZON_COLUMNS for the Amazon Sale Order Template.
        Covers: asin, item-price, quantity, ship-state, purchase-date, amazon-order-id, fulfillment-channel
        """
        errors = []
        if df.empty:
            return ["Amazon Sale Order Template is completely empty."]

        for index, row in df.iterrows():
            row_num = index + 1

            # Presence check for all essential operational columns
            required_cols = ['asin',  'quantity', 'ship-state', 'purchase-date', 'amazon-order-id']
            for col in required_cols:
                if cls.is_null(row.get(col)):
                    errors.append(f"Row {row_num}: Required column '{col}' is missing or null in Amazon Sale Order Template.")

            # Data-type validation for 'quantity'
            qty = row.get('quantity')
            if not cls.is_null(qty):
                if not cls.is_numeric(qty) or float(qty) < 0:
                    errors.append(f"Row {row_num}: Column 'quantity' must be a positive integer. Found value: '{qty}'.")

            # Format validation for 'purchase-date' (ISO Format)
            p_date = row.get('purchase-date')
            if not cls.is_null(p_date) and not cls.is_valid_iso_date(p_date):
                errors.append(f"Row {row_num}: Column 'purchase-date' has an invalid ISO timestamp format. Found value: '{p_date}'. Expected format: 'YYYY-MM-DDTHH:MM:SS'.")

        return errors

    @classmethod
    def validate_product_bundle(cls, df: pd.DataFrame) -> list:
        """Validates configuration pairs and breakdown weights inside the Product Bundle config sheet."""
        errors = []
        if df.empty:
            return ["Product Bundle configuration sheet is completely empty."]

        for index, row in df.iterrows():
            row_num = index + 1
            for col in REQUIRED_BUNDLE_COLUMNS:
                if cls.is_null(row.get(col)):
                    errors.append(f"Row {row_num}: Required column '{col}' is missing or null in Product Bundle Configuration.")

            # Validate structural bundle quantity weights
            bundle_qty = row.get('Qty (Product Bundle Item)')
            if not cls.is_null(bundle_qty) and not cls.is_numeric(bundle_qty):
                errors.append(f"Row {row_num}: Column 'Qty (Product Bundle Item)' must be numeric. Found value: '{bundle_qty}'.")
                
        return errors