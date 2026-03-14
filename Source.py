import customtkinter as ctk
import requests
import time
import base64

latest_prices = {}
last_update_time = None

contract_address = None
meme_price = None
meme_symbol = None
meme_name = None
last_meme_update = None

port_address = None
port_balance = None
port_value = None
last_port_update = None

# MAIN TRACKER ----------------------------------------------
def optionmenu_callback(choice):
    update_displayed_price()

def fetch_all_prices():
    global latest_prices, last_update_time
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,solana,ethereum",
            "vs_currencies": "usd"
        }
        headers = {"x-cg-demo-api-key": "CG-YOUR-API-KEY"}
        response = requests.get(url, params=params, headers=headers, timeout=6)

        if response.status_code == 429:
            print("Rate limited (429) - waiting a bit longer next time")
            return False
        
        response.raise_for_status()
        data = response.json()

        latest_prices = {
            "bitcoin": data["bitcoin"]["usd"],
            "solana": data["solana"]["usd"],
            "ethereum": data["ethereum"]["usd"]
        }
        
        last_update_time = time.strftime('%H:%M:%S')
        return latest_prices
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price: {e}")
        return False

def update_displayed_price():
    choice = combobox.get()
    
    if choice == "Bitcoin(BTC) Price":
        coin = "bitcoin"
    elif choice == "Solana(SOL) Price":
        coin = "solana"
    else:
        coin = "ethereum"

    price = latest_prices.get(coin)
    if price is not None:
        price_label.configure(text=f"${price:,.2f}")
        if last_update_time:
            status_label.configure(text=f"Last updated: {last_update_time}")
    else:
        price_label.configure(text="No data yet")
        status_label.configure(text="Waiting for update...")

def refresh_data():
    success = fetch_all_prices()
    update_displayed_price()

    app.after(25000, refresh_data)

#----------------------------------------------

# MEME TRACKER ----------------------------------------------
def button_callback():
    contract_address = CAtbox.get("0.0", "end")
    fetch_meme_price(contract_address)

def fetch_meme_price(CA):
    global meme_price, last_meme_update
    try:
        murl = "https://open-api.openocean.finance/v4/solana/quote"
        mparams = {
            'inTokenAddress': CA.strip(), 
            'outTokenAddress': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
            'amountDecimals': '1000000000',
            'gasPrice': '0',
        }

        response = requests.get(murl, params=mparams, timeout=10)
        response.raise_for_status()

        data = response.json()

        print("Full API response:", data)

        if data.get("code") != 200:
            error_msg = data.get("msg", "Unknown error from OpenOcean")
            print(f"API error: {error_msg}")
            return False

        quote_data = data.get("data")
        if not quote_data or "inToken" not in quote_data:
            print("Unexpected response format - no 'data.inToken'")
            print(data)
            return False

        in_token = quote_data["inToken"]
        if "usd" not in in_token:
            print("No 'usd' price in inToken")
            return False

        meme_price = float(in_token["usd"])
        meme_name = in_token.get("name", "Unknown")
        meme_symbol = in_token.get("symbol", "???")
        last_meme_update = time.strftime('%H:%M:%S')

        mprice_label.configure(text=f"${meme_price:,.6f}")
        mstatus_label.configure(text=f"Last updated: {last_meme_update} | {meme_symbol}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"Network/request error: {e}")
        mstatus_label.configure(text=f"Network error: {str(e)}")
        return False

    except (KeyError, TypeError, ValueError) as e:
        print(f"Data parsing error: {e}")
        print("Full response was:", data if 'data' in locals() else "not received")
        mstatus_label.configure(text="Invalid API response")
        return False
#----------------------------------------------

# PORTFOLIO TRACKER ----------------------------------------------

def p_button_callback():
    global port_address
    port_address = Atbox.get("0.0", "end").strip()

    if not port_address:
        pstatus_label.configure(text="Please enter a valid Solana address")
        return
    else:
        fetch_portfolio_balance(port_address)

def fetch_portfolio_balance(PA):
    global port_balance, last_port_update, port_value

    sol = latest_prices.get("solana")

    API_K = 'YOUR-API-KEY'
    WALLET = PA
    api_key_transformed = base64.b64encode(f'{API_K}:'.encode()).decode()

    url = f"https://api.zerion.io/v1/wallets/{WALLET}/portfolio"


    headers = {
        "Authorization": f"Basic {api_key_transformed}",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    if response.status_code != 200:
        print(f"API error: {response.status_code, response.text}")
        return False

    data = response.json()

    last_port_update = time.strftime('%H:%M:%S')
    port_balance = data["data"]["attributes"]["total"]["positions"]
    port_value = port_balance * sol

    mstatus_label.configure(text=f"Last updated: {last_port_update}")
    bal_label.configure(text=f"Balance: {port_balance:,.2f} solana")
    val_label.configure(text=f"Value: ${port_value:,.2f}")


#----------------------------------------------

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
app.geometry("600x320")
app.title("Coinso")

tabview = ctk.CTkTabview(master=app)
tabview.pack(fill="both", expand=True)

maintab = tabview.add("Main Tracker")
memetab = tabview.add("Meme Tracker")
porttab = tabview.add("Portfolio Tracker")

# MAIN TAB ----------------------------------------------
combobox = ctk.CTkOptionMenu(master=maintab,
                                       values=["Bitcoin(BTC) Price", "Solana(SOL) Price", "Ethereum(ETH) Price"],
                                       command=optionmenu_callback)
combobox.pack(padx=20, pady=10)
combobox.set("Bitcoin(BTC) Price")




price_label = ctk.CTkLabel(master=maintab, text="Loading...", font=ctk.CTkFont(size=28, weight="bold"), text_color="lime")
price_label.place(relx=0.5, rely=0.5, anchor="center")

status_label = ctk.CTkLabel(master=maintab, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
status_label.pack(side="bottom", pady=10)
#----------------------------------------------

# MEME TAB ----------------------------------------------
CAtbox = ctk.CTkTextbox(master=memetab, height=50)
CAtbox.place(relx=0.5, anchor="n")

trackButton = ctk.CTkButton(master=memetab, text="Track Memecoin", command=button_callback)
trackButton.place(relx=0.5, rely=0.3, anchor="n")

mprice_label = ctk.CTkLabel(master=memetab, text="Waiting...", font=ctk.CTkFont(size=28, weight="bold"), text_color="lime")
mprice_label.place(relx=0.5, rely=0.75, anchor="center")

mstatus_label = ctk.CTkLabel(master=memetab, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
mstatus_label.pack(side="bottom", pady=10)
#----------------------------------------------

# PORTFOLIO TAB ----------------------------------------------
Atbox = ctk.CTkTextbox(master=porttab, height=50)
Atbox.place(relx=0.5, anchor="n")

trackButton = ctk.CTkButton(master=porttab, text="Track Portfolio", command=p_button_callback)
trackButton.place(relx=0.5, rely=0.3, anchor="n")

bal_label = ctk.CTkLabel(master=porttab, text="Waiting...", font=ctk.CTkFont(size=28, weight="bold"), text_color="lime")
bal_label.place(relx=0.5, rely=0.75, anchor="center")

val_label = ctk.CTkLabel(master=porttab, text="", font=ctk.CTkFont(size=28, weight="bold"), text_color="lime")
val_label.place(relx=0.5, rely=0.85, anchor="center")

pstatus_label = ctk.CTkLabel(master=porttab, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
pstatus_label.pack(side="bottom", pady=10)
#----------------------------------------------

fetch_all_prices()
refresh_data()

app.mainloop()
