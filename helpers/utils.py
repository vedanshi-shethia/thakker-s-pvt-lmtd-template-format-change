import re

def extract_pack_of_quantity(item_id):
    match = re.search(r'\(Pack of (\d+)\)', item_id)
    return int(match.group(1)) if match else 1


def calculate_price_per_packet(total_amount, pack_of_quantity, product_bundle_quantity, amazon_quantity):
    if pack_of_quantity * product_bundle_quantity * amazon_quantity == 0:
        return 0
    return total_amount / (pack_of_quantity * product_bundle_quantity * amazon_quantity)


def format_state(state):
    if not state or isinstance(state, float):
        return "Unknown"
    return state.strip().title()
