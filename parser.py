import re
import json
from pathlib import Path
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])
    return text

def parse_statement(text):
    data = {}

    # 1. Extract account info
    account_info = re.search(r"STATEMENT DATE:\s+(.*?)\s+GMI ACCOUNT NUMBER:\s+(.*?)\s+([\s\S]+?)\n", text)
    if account_info:
        data['statement_date'] = account_info.group(1).strip()
        data['account_number'] = account_info.group(2).strip()
        data['name_address'] = account_info.group(3).strip().replace('\n', ', ')

    # 2. Extract trades with contract and direction
    trade_lines = re.findall(
        r"(\d{1,2}/\d{1,2}/\d)\s+US\s+(?:(\d*)\s*)?(?:(\d*)\s+)?(JUN \d{2} CME MICRO S&P)\s+\d+\s+([\d.]+)", 
        text
    )

    grouped_trades = {}
    for t in trade_lines:
        date = t[0]
        buy_qty = int(t[1]) if t[1].strip() else 0
        sell_qty = int(t[2]) if t[2].strip() else 0
        contract = t[3].strip()
        price = float(t[4])
        direction = "BUY" if buy_qty > 0 else "SELL"

        key = f"{date} - {contract}"
        grouped_trades.setdefault(key, []).append({
            "date": date,
            "contract": contract,
            "direction": direction,
            "quantity": buy_qty if buy_qty > 0 else sell_qty,
            "price": price
        })

    data['trades'] = grouped_trades


    # 3. Extract fees
    fees = {
        'commission': re.search(r'COMMISSION\s+US\s+([\d.]+)-', text),
        'exchange_fee': re.search(r'EXCHANGE FEE\s+US\s+([\d.]+)-', text),
        'nfa_fee': re.search(r'NFA FEE\s+US\s+([\d.]+)-', text),
        'total_fees': re.search(r'TOTAL COMMISSION AND FEES\s+([\d.]+)-', text),
    }
    data['fees'] = {k: float(v.group(1)) if v else 0.0 for k, v in fees.items()}

    # 4. Gross profit or loss
    gpl = re.search(r'GROSS PROFIT OR LOSS\s+US\s+([\d.-]+)', text)
    data['gross_profit_loss'] = float(gpl.group(1)) if gpl else 0.0

    # 5. Balances
    balances = {
        'beginning_balance': re.search(r'BEGINNING BALANCE\s+([\d.]+)', text),
        'ending_balance': re.search(r'ENDING BALANCE\s+([\d.]+)', text),
        'total_equity': re.search(r'TOTAL EQUITY\s+([\d.]+)', text),
        'account_value': re.search(r'ACCOUNT VALUE AT MARKET\s+([\d.]+)', text),
        'excess_equity': re.search(r'EXCESS EQUITY\s+([\d.]+)', text),
    }
    data['balances'] = {k: float(v.group(1)) if v else 0.0 for k, v in balances.items()}

    # 6. Journal entries
    journals = re.findall(r"JOURNAL DESCRIPTION\s+.*?\n\s*\d+/\d+/\d+\s+US\s+.*?Futures Cash Sweep\s+US\s+([\d.]+)-", text)
    data['journal_entries'] = [{"description": "Futures Cash Sweep", "amount": -float(j)} for j in journals]

    return data

def main():
    pdf_path = "document.pdf"  # Replace with your file path
    text = extract_text_from_pdf(pdf_path)
    statement_data = parse_statement(text)

    json_output = Path("parsed_statement.json")
    with json_output.open("w") as f:
        json.dump(statement_data, f, indent=4)
    print(f"Parsed data written to {json_output.resolve()}")

if __name__ == "__main__":
    main()
