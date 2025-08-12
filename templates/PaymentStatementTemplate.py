import pandas as pd
import re
from datetime import datetime
from helpers.utils import extract_pack_of_quantity, calculate_price_per_packet, format_state
from helpers.file_handler import FileHandler

class Constants:
    SERIES_FORMAT = "ACC-JV-.YYYY.-"
    ACCOUNT_27_COD = "1604 - Amazon COD Fund - TMPL"
    ACCOUNT_29_COD = "1604 - Amazon COD Fund - TMPL29"
    ACCOUNT_27_ELECTRONIC = "1601 - Amazon Electronic Fund - TMPL"
    ACCOUNT_29_ELECTRONIC = "1601 - Amazon Electronic Fund - TMPL29"
    CREDITORS = ["Creditors (INR) - TMPL", "Creditors (INR) - TMPL29"]
    DEBTORS = ["Debtors (INR) - TMPL", "Debtors (INR) - TMPL29"]

def parse_date(date_str, input_format="%d.%m.%Y %H:%M:%S %Z", output_format="%Y/%m/%d"):
    return datetime.strptime(date_str, input_format).strftime(output_format)

def get_accounting_entry(company_gstin, match_template):
    if re.match(r"^27\d*", company_gstin):
        return match_template.iloc[0]["ERP 27 Company "]
    elif re.match(r"^29\d*", company_gstin):
        return match_template.iloc[0]["ERP 29 Company "]
    return "" 

class PaymentStatementTemplate:
    def __init__(self, payment_statement_file, sale_register_file, matching_template_file):
        self.payment_statement = FileHandler.read_excel(payment_statement_file)
        self.sale_register = FileHandler.read_excel(sale_register_file)
        self.matching_template = FileHandler.read_excel(matching_template_file)

    def process(self, order_type, expense):

        output_rows, error_rows = [], []
        processed_orders = set()
        expense = expense.split(',')
        total_expense_amount = 0
        principle_record = {}
        total_debit = 0
        total_credit = 0

        settlement_start_date = parse_date(self.payment_statement.iloc[0]["settlement-start-date"])
        settlement_end_date = parse_date(self.payment_statement.iloc[0]["settlement-end-date"])
        
        self.payment_statement = self.payment_statement.iloc[1:].reset_index(drop=True)
        self.payment_statement.sort_values(by=["order-id"], inplace=True)
        order_sums = self.payment_statement.groupby("order-id", as_index=False)["amount"].sum()
        last_occurrence = self.payment_statement.reset_index().groupby("order-id")["index"].last().to_dict()

        
        for index, order in self.payment_statement.iterrows():
            order_id = order.get("order-id")
            posting_date = datetime.strptime(str(order["posted-date"]), "%d.%m.%Y").strftime("%Y-%m-%d")

            #For orders that do not have an order id.
            if pd.isna(order_id):

                amount = order.get("amount")

                if order["amount-description"] == "Current Reserve Amount" or order["amount-description"] == "Previous Reserve Amount Balance":

                    account_entry_debit = account_entry_credit = ""
                    if order_type == "Electronic_" :
                        account_entry_debit = "1601 - Amazon Electronic Fund - TMPL"
                        account_entry_credit = "1602 - Amazon Freeze Fund - Electronic - TMPL"

                    elif order_type == "COD_" :
                        account_entry_debit = "1604 - Amazon COD Fund - TMPL"
                        account_entry_credit = "1603 - Amazon Freeze Fund - COD - TMPL"               

                    output_rows.append({
                        "Company" : "Thakker Mercantile Private Limited",
                        "Entry Type": "Contra Entry",
                        "Posting Date": posting_date,
                        "Series": Constants.SERIES_FORMAT,
                        "Reference Date" : posting_date,
                        "Cost Center (Accounting Entries)" : "6 - Retail - TMPL",
                        "Account (Accounting Entries)": account_entry_debit,
                        "Debit (Accounting Entries)": max(amount, 0),
                        "Credit (Accounting Entries)": min(amount, 0) * -1,

                    })

                    output_rows.append({
                        "Account (Accounting Entries)": account_entry_credit,
                        "Debit (Accounting Entries)": min(amount, 0) * -1,
                        "Credit (Accounting Entries)": max(amount, 0),
                    })

                continue
            
            # For order that have id
            order_id_match = self.sale_register[self.sale_register["Customer's Purchase Order"] == order_id]
            amount_description_match = self.matching_template[self.matching_template["amount-description"] == order["amount-description"]]
            
            if order_id_match.empty:
                error_rows.append({"Reference Number": f"Error: No customer's Purchase Order for {order_id}"})
                continue
            if amount_description_match.empty:
                error_rows.append({"Account (Accounting Entries)": f"Error: No match for {order["amount-description"]}"})
                continue
            
            company_gstin = str(order_id_match.iloc[0]["Company GSTIN"])
            account_entry = get_accounting_entry(company_gstin, amount_description_match)


            debit_entry = order["amount"] if order["amount"] < 0 else 0
            credit_entry = order["amount"] if order["amount"] >= 0 else 0
            
            party, party_type, reference_name, reference_type = "", "", "", ""
            if account_entry in Constants.CREDITORS:
                party, party_type = "Amazon Seller Services Private Limited", "Supplier"
            elif account_entry in Constants.DEBTORS:
                party, party_type = order_id_match.iloc[0]["Customer Name"], "Customer"
                reference_name = order_id_match.iloc[0]["Voucher"]
                reference_type = order_id_match.iloc[0]["Voucher Type"]
            
            reference_date = datetime.strptime(str(order_id_match.iloc[0]["Posting Date"]), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
            user_remark = f"{order_id} {settlement_start_date} - {settlement_end_date}"

            if(order["amount-description"] in expense):
                total_expense_amount += order["amount"]

            if order["amount-description"] not in expense:

                if(order["amount-description"] in "Principal") :
                    principle_record = {
                        "Account (Accounting Entries)": account_entry,
                        "Cost Center (Accounting Entries)": order_id_match.iloc[0]["Cost Center"],
                        "Debit (Accounting Entries)": debit_entry * -1,
                        "Credit (Accounting Entries)": credit_entry,
                        "Party (Accounting Entries)": party,
                        "Party Type (Accounting Entries)": party_type,
                        "Reference Name (Accounting Entries)": reference_name,
                        "Reference Type (Accounting Entries)": reference_type,
                    }
                    

                elif order_id in processed_orders:
                
                    output_rows.append({
                        "Account (Accounting Entries)": account_entry,
                        "Cost Center (Accounting Entries)": order_id_match.iloc[0]["Cost Center"],
                        "Debit (Accounting Entries)": debit_entry * -1,
                        "Credit (Accounting Entries)": credit_entry,
                        "Party (Accounting Entries)": party,
                        "Party Type (Accounting Entries)": party_type,
                        "Reference Name (Accounting Entries)": reference_name,
                        "Reference Type (Accounting Entries)": reference_type,
                        "User Remark (Accounting Entries)": order["amount-type"] + "|" + order["amount-description"]
                    })

                    total_credit += credit_entry
                    total_debit += debit_entry * -1
                else:
                    output_rows.append({
                        "Company": order_id_match.iloc[0]["Company"],
                        "Entry Type": "Bank Entry",
                        "Posting Date": posting_date,
                        "Series": Constants.SERIES_FORMAT,
                        "Reference Date": reference_date,
                        "Reference Number": order_id,
                        "User Remark": user_remark,
                        "Company GSTIN": company_gstin,
                        "Account (Accounting Entries)": account_entry,
                        "Cost Center (Accounting Entries)": order_id_match.iloc[0]["Cost Center"],
                        "Debit (Accounting Entries)": debit_entry * -1,
                        "Credit (Accounting Entries)": credit_entry,
                        "Party (Accounting Entries)": party,
                        "Party Type (Accounting Entries)": party_type,
                        "Reference Name (Accounting Entries)": reference_name,
                        "Reference Type (Accounting Entries)": reference_type,
                        "User Remark (Accounting Entries)": order["amount-type"] + "|" + order["amount-description"]
                    })

                    total_credit += credit_entry
                    total_debit += debit_entry * -1
                    processed_orders.add(order_id)
                
                
            # For the last row of a same order to sum all the amount and cancle evrything out. If positive then Debit and negative then debit.
            if order_id in last_occurrence and index == last_occurrence[order_id]:

                
                principle_record["Credit (Accounting Entries)"] += total_expense_amount

                principle_record["Credit (Accounting Entries)"] = round(principle_record["Credit (Accounting Entries)"], 2)
                
                total_credit += principle_record["Credit (Accounting Entries)"]

                account_accounting_entries_for_end_total = ''

                total_amount = order_sums.loc[order_sums['order-id'] == order_id, 'amount'].values[0]
                if order_type == 'COD_':
                    if re.match(r"^27\d*", company_gstin):
                        account_accounting_entries_for_end_total = '1604 - Amazon COD Fund - TMPL'
                    if re.match(r"^29\d*", company_gstin):
                        account_accounting_entries_for_end_total = '1604 - Amazon COD Fund - TMPL29'

                if order_type == 'Electronic_':
                    if re.match(r"^27\d*", company_gstin):
                        account_accounting_entries_for_end_total = '1601 - Amazon Electronic Fund - TMPL'
                    if re.match(r"^29\d*", company_gstin):
                        account_accounting_entries_for_end_total = '1601 - Amazon Electronic Fund - TMPL29'

                credit_entry_for_end_total = min(total_amount, 0) * -1
                debit_entry_for_end_total =  max(total_amount, 0)

                total_credit += credit_entry_for_end_total
                total_debit += debit_entry_for_end_total

                total_credit = round(total_credit, 2)
                total_debit = round(total_debit, 2)  

                if(total_debit != total_credit) :
                    error_rows.append({"Credit (Accounting Entries)": F"Total debit and Total credit do not match for {order_id}"})

                difference = round(total_credit) - total_credit
                difference = round(difference, 2)

                print("Total Credit : ", total_credit)
                print("Total Debit : ", total_debit)

                print("Round off : ", difference)

                if(difference != 0) :

                    credit_entry = min(difference, 0) * -1
                    debit_entry =  max(difference, 0)
                    
                    account_accounting_entries = ''

                    if re.match(r"^27\d*", company_gstin):
                        account_accounting_entries = 'Rounded Off - TMPL27'
                    if re.match(r"^29\d*", company_gstin):
                        account_accounting_entries = 'Rounded Off - TMPL29'

                    output_rows.append({
                        "Account (Accounting Entries)": account_accounting_entries,
                        "Cost Center (Accounting Entries)": order_id_match.iloc[0]["Cost Center"],
                        "Debit (Accounting Entries)":debit_entry,
                        "Credit (Accounting Entries)": credit_entry,
                    })

                

                if (difference < 0):
                    debit_entry_for_end_total += difference
                    principle_record["Credit (Accounting Entries)"] += difference * 2
                    principle_record["Credit (Accounting Entries)"] = round(principle_record["Credit (Accounting Entries)"], 2)
                    principle_record["User Remark (Accounting Entries)"] = "ItemPrice|Principle " + "("+ str(principle_record["Credit (Accounting Entries)"]) + ")" + "- [Expense: "+ str(total_expense_amount) +"]" + "- [Roundoff: "+ str(difference * 2) + "]" 
                elif (difference > 0):
                    principle_record["Credit (Accounting Entries)"] += difference
                    principle_record["Credit (Accounting Entries)"] = round(principle_record["Credit (Accounting Entries)"], 2)
                    principle_record["User Remark (Accounting Entries)"] = "ItemPrice|Principle " + "("+ str(principle_record["Credit (Accounting Entries)"]) + ")" + "- [Expense: "+ str(total_expense_amount) +"]" + "- [Roundoff: "+ str(difference) + "]" 

                output_rows.append(principle_record)

                output_rows.append({
                    "Account (Accounting Entries)": account_accounting_entries_for_end_total,
                    "Cost Center (Accounting Entries)": order_id_match.iloc[0]["Cost Center"],
                    "Debit (Accounting Entries)":debit_entry_for_end_total,
                    "Credit (Accounting Entries)": credit_entry_for_end_total,
                })
                
                total_expense_amount = 0
                total_credit = 0
                total_debit = 0

        # For the order that don't have order id and are of type Advertisement and business sdvisory !
        null_orders = self.payment_statement[pd.isna(self.payment_statement["order-id"]) & 
                                            self.payment_statement["amount-type"].isin(["Cost of Advertising", "Amazon Business Advisory Fee"])]
        null_orders.sort_values(by=["posted-date"], inplace=True)

        posted_dates = set()

        grouped_null_orders = null_orders.groupby("posted-date", sort=False)
        for posted_date, group in grouped_null_orders:
            posted_date = datetime.strptime(posted_date, "%d.%m.%Y").strftime("%Y-%m-%d")
            total_amount = group["amount"].sum()
            
            for _, order in group.iterrows():
                amount = order["amount"]
                if posted_date in posted_dates:
                    output_rows.append({
                        "Account (Accounting Entries)": "Creditors (INR) - TMPL",
                        "Cost Center (Accounting Entries)": "6 - Retail - TMPL",
                        "Debit (Accounting Entries)": min(amount, 0) * -1,
                        "Credit (Accounting Entries)": max(amount, 0),
                        "Party (Accounting Entries)": "Amazon Seller Services Private Limited",
                        "Party Type (Accounting Entries)": "Supplier"
                    })

                else:
                    output_rows.append({
                        "Company": "Thakker Mercantile Private Limited",
                        "Entry Type": "Contra Entry",
                        "Posting Date": posted_date,
                        "Series": Constants.SERIES_FORMAT,
                        "Reference Date": posted_date,
                        "Reference Number": f"{settlement_start_date} - {settlement_end_date} - {order["amount-type"]}",
                        "User Remark": f"{settlement_start_date} - {settlement_end_date}",
                        "Company GSTIN": "27AACCT1557E1ZH",
                        "Account (Accounting Entries)": "Creditors (INR) - TMPL",
                        "Cost Center (Accounting Entries)": "6 - Retail - TMPL",
                        "Debit (Accounting Entries)": min(amount, 0) * -1,
                        "Credit (Accounting Entries)": max(amount, 0),
                        "Party (Accounting Entries)": "Amazon Seller Services Private Limited",
                        "Party Type (Accounting Entries)": "Supplier"
                    })
                    posted_dates.add(posted_date)
            
            
                accounting_entry = ""
                if order_type == "Electronic_" :
                    accounting_entry = "1601 - Amazon Electronic Fund - TMPL"

                elif order_type == "COD_" :
                    accounting_entry = "1603 - Amazon Freeze Fund - COD - TMPL"  

            output_rows.append({
                "Account (Accounting Entries)": accounting_entry,
                "Cost Center (Accounting Entries)": "6 - Retail - TMPL",
                "Debit (Accounting Entries)": 0,
                "Credit (Accounting Entries)": total_amount * -1,
            })
        
        return pd.DataFrame(output_rows), pd.DataFrame(error_rows)
