import pandas as pd


class FileHandler:
    @staticmethod
    def read_excel(file):
        try:
            return pd.read_excel(file)
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

    @staticmethod
    def validate_columns(df, required_columns, file_name="File"):
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"{file_name} is missing columns: {', '.join(missing)}")
        return True
