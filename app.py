import streamlit as st
import yfinance as yf
import pandas as pd
import re
import plotly.graph_objects as go
import plotly.express as px
import time
import random
from datetime import datetime

st.set_page_config(page_title="Financial Statement Analyzer", layout="wide")

# Initialize session state variables
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = False
if 'step' not in st.session_state:
    st.session_state.step = 'input'
if 'ticker' not in st.session_state:
    st.session_state.ticker = ''
if 'annual_income_statement' not in st.session_state:
    st.session_state.annual_income_statement = None
if 'income_mapping_user' not in st.session_state:
    st.session_state.income_mapping_user = None

st.title("📊 Financial Statement Analyzer")
st.write("Analisi dell'Income Statement da Yahoo Finance")

###############################################
# DEMO DATA
###############################################

# Sample data for demo mode when API is rate limited
DEMO_COMPANY_INFO = {
    "AAPL": {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "currentPrice": 174.79,
        "marketCap": 2740000000000,
        "logo_url": "https://logo.clearbit.com/apple.com"
    },
    "MSFT": {
        "longName": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software—Infrastructure",
        "currentPrice": 403.78,
        "marketCap": 3000000000000,
        "logo_url": "https://logo.clearbit.com/microsoft.com"
    },
    "GOOGL": {
        "longName": "Alphabet Inc.",
        "sector": "Communication Services",
        "industry": "Internet Content & Information",
        "currentPrice": 153.05,
        "marketCap": 1900000000000,
        "logo_url": "https://logo.clearbit.com/google.com"
    }
}

# Sample financial data structure for demo mode
DEMO_FINANCIAL_DATA = {
    "AAPL": {
        "financials": {
            "Revenue": [394328000000, 365817000000, 274515000000, 260174000000],
            "Cost Of Revenue": [226107000000, 208168000000, 152836000000, 161782000000],
            "Gross Profit": [168221000000, 157649000000, 121679000000, 98392000000],
            "Selling General And Administration": [26474000000, 25094000000, 21973000000, 19916000000],
            "Research And Development": [29915000000, 26251000000, 21914000000, 18752000000],
            "Operating Income": [111832000000, 109552000000, 94680000000, 66288000000],
            "Pretax Income": [113645000000, 109272000000, 94680000000, 67091000000],
            "Income Tax Expense": [18573000000, 14089000000, 14527000000, 9680000000],
            "Net Income": [95025000000, 99803000000, 94680000000, 57411000000],
            "Diluted EPS": [6.14, 6.11, 5.61, 3.28]
        },
        "dates": ["2023-09-30", "2022-09-30", "2021-09-30", "2020-09-30"]
    },
    "MSFT": {
        "financials": {
            "Revenue": [211915000000, 198270000000, 168088000000, 143015000000],
            "Cost Of Revenue": [70950000000, 65812000000, 52232000000, 46078000000],
            "Gross Profit": [140965000000, 132458000000, 115856000000, 96937000000],
            "Selling General And Administration": [42513000000, 39585000000, 35327000000, 29539000000],
            "Research And Development": [27155000000, 24512000000, 20716000000, 19269000000],
            "Operating Income": [88389000000, 83383000000, 69916000000, 52959000000],
            "Pretax Income": [88092000000, 83386000000, 71102000000, 53036000000],
            "Income Tax Expense": [10605000000, 10978000000, 9831000000, 8755000000],
            "Net Income": [77487000000, 72738000000, 61271000000, 44281000000],
            "Diluted EPS": [10.31, 9.65, 8.05, 5.76]
        },
        "dates": ["2023-06-30", "2022-06-30", "2021-06-30", "2020-06-30"]
    },
    "GOOGL": {
        "financials": {
            "Revenue": [307394000000, 282836000000, 257637000000, 182527000000],
            "Cost Of Revenue": [131380000000, 126203000000, 110939000000, 84732000000],
            "Gross Profit": [176014000000, 156633000000, 146698000000, 97795000000],
            "Selling General And Administration": [45567000000, 43026000000, 37702000000, 31023000000],
            "Research And Development": [44861000000, 39500000000, 31562000000, 27573000000],
            "Operating Income": [84486000000, 73972000000, 78714000000, 41224000000],
            "Pretax Income": [84800000000, 76033000000, 86692000000, 42733000000],
            "Income Tax Expense": [11907000000, 13118000000, 14701000000, 7813000000],
            "Net Income": [73800000000, 59972000000, 76033000000, 40269000000],
            "Diluted EPS": [5.80, 4.56, 5.61, 2.93]
        },
        "dates": ["2023-12-31", "2022-12-31", "2021-12-31", "2020-12-31"]
    }
}

# Function to get demo financial data
def get_demo_financial_data(ticker):
    """Get demo financial data for a ticker"""
    if ticker in DEMO_FINANCIAL_DATA:
        return DEMO_FINANCIAL_DATA[ticker]
    # Default to AAPL if ticker not in demo data
    return DEMO_FINANCIAL_DATA["AAPL"]

# Function to get demo company info
def get_demo_company_info(ticker):
    """Get demo company info for a ticker"""
    if ticker in DEMO_COMPANY_INFO:
        return DEMO_COMPANY_INFO[ticker]
    # Default to AAPL if ticker not in demo data
    return DEMO_COMPANY_INFO["AAPL"]

###############################################
# CONFIGURAZIONE – Income Statement Mapping
###############################################

config = {
    "income_mapping": {
        "Revenue": ["Total Revenue", "Operating Revenue"],
        "Total COGS": ["Cost Of Revenue"],
        "Gross Profit": ["Gross Profit"],
        "SG&A": ["Selling General And Administration", "General & Administrative"],
        "R&D": ["Research And Development"],
        "S&M": ["Sales And Marketing", "Selling and Marketing", "Selling Expenses", "Marketing Expense"],
        "Operating Income": ["Operating Income"],
        "Pretax Income": ["Pretax Income"],
        "Taxes": ["Income Tax Expense", "Taxes"],
        "Net Income": ["Net Income"],
        "EPS": ["Diluted EPS"],
        "Net Interest Income": ["Net Non Operating Interest Income Expense", "Other Income Expense"]
    }
}

###############################################
# FUNZIONE DI CREAZIONE GRAFICI CON PLOTLY
###############################################

def create_charts(df):
    """Create charts from the data"""
    # Create a copy for chart formatting
    chart_df = df.copy()
    
    # 1. Revenue & Net Income Chart
    fig1 = go.Figure()
    
    if "Revenue" in chart_df.columns:
        fig1.add_trace(go.Bar(
            x=chart_df.index,
            y=chart_df["Revenue"],
            name="Revenue",
            marker_color='rgb(55, 83, 109)'
        ))
    
    if "Net Income" in chart_df.columns:
        fig1.add_trace(go.Bar(
            x=chart_df.index,
            y=chart_df["Net Income"],
            name="Net Income",
            marker_color='rgb(26, 118, 255)'
        ))
    
    fig1.update_layout(
        title="Revenue & Net Income (in millions)",
        xaxis_title="Year",
        yaxis_title="Amount (in millions)",
        barmode='group',
        legend=dict(x=0, y=1.0),
        template="plotly_white"
    )
    
    # 2. Margins & Tax Percentage Chart (aggiunto il Tax Percentage qui)
    fig2 = go.Figure()
    
    # Aggiungi i margini
    for margin in ["Gross Margin", "Operating Margin", "Net Margin"]:
        if margin in chart_df.columns:
            # Handle string percentage values
            if chart_df[margin].dtype == 'object':
                margin_values = chart_df[margin].apply(lambda x: float(x.strip('%')) if isinstance(x, str) else x)
            else:
                margin_values = chart_df[margin]
                
            fig2.add_trace(go.Scatter(
                x=chart_df.index,
                y=margin_values,
                mode='lines+markers',
                name=margin
            ))
    
    # Aggiungi Tax Percentage al grafico dei margini
    if "Tax Percentage" in chart_df.columns:
        if chart_df["Tax Percentage"].dtype == 'object':
            tax_values = chart_df["Tax Percentage"].apply(lambda x: float(x.strip('%')) if isinstance(x, str) else x)
        else:
            tax_values = chart_df["Tax Percentage"]
            
        fig2.add_trace(go.Scatter(
            x=chart_df.index,
            y=tax_values,
            mode='lines+markers',
            name="Tax Percentage",
            marker_color='rgb(255, 127, 14)'  # Orange
        ))
    
    fig2.update_layout(
        title="Profit Margins & Tax Percentage (%)",
        xaxis_title="Year",
        yaxis_title="Percentage (%)",
        legend=dict(x=0, y=1.0),
        template="plotly_white"
    )
    
    # 3. YoY Growth Chart
    fig3 = go.Figure()
    
    for growth in ["Revenue Y/Y", "Net Income Y/Y"]:
        if growth in chart_df.columns:
            # Handle string percentage values
            if chart_df[growth].dtype == 'object':
                growth_values = chart_df[growth].apply(lambda x: float(x.strip('%')) if isinstance(x, str) else x)
            else:
                growth_values = chart_df[growth]
                
            fig3.add_trace(go.Scatter(
                x=chart_df.index,
                y=growth_values,
                mode='lines+markers',
                name=growth
            ))
    
    fig3.update_layout(
        title="Year-over-Year Growth (%)",
        xaxis_title="Year",
        yaxis_title="Growth (%)",
        legend=dict(x=0, y=1.0),
        template="plotly_white"
    )
    
    return fig1, fig2, fig3

###############################################
# FUNZIONI DI MAPPING E VALUTAZIONE
###############################################

def transform_expr(user_input, available):
    """
    Sostituisce ogni numero (indice) nell'input con il nome della colonna corrispondente
    (racchiuso tra backtick), basandosi sulla lista available.
    """
    def repl(match):
        idx = int(match.group(0))
        if idx <= len(available):
            return f"`{available[idx-1]}`"
        else:
            return match.group(0)
    return re.sub(r'\b\d+\b', repl, user_input)

def display_candidates_with_values(df, candidate_list, quarterly_df=None):
    """
    Visualizza le colonne candidate con i loro valori per l'ultimo periodo disponibile.
    Se i dati trimestrali non sono disponibili, usa l'ultimo anno.
    
    Args:
        df: DataFrame con i dati annuali
        candidate_list: Lista di colonne candidate
        quarterly_df: DataFrame con i dati trimestrali (opzionale)
    """
    if df.empty:
        return {}
    
    # Determina quale DataFrame usare per i valori
    display_df = quarterly_df if quarterly_df is not None else df
    latest = display_df.iloc[0]  # Prima riga (più recente)
    
    # Indica la fonte dei dati per migliore comprensione
    source = "trimestre" if quarterly_df is not None else "anno"
    
    results = {}
    for i, col in enumerate(candidate_list, start=1):
        try:
            # Verifica se la colonna esiste
            if col in display_df.columns:
                # Accedi al valore
                raw_value = latest[col]
                
                # Formatta il valore in base al tipo
                if pd.notna(raw_value):
                    if isinstance(raw_value, (int, float)):
                        formatted_value = f"${raw_value/1e6:.2f}M"
                    else:
                        # Tenta conversione a float se è una stringa
                        try:
                            num_value = float(raw_value)
                            formatted_value = f"${num_value/1e6:.2f}M"
                        except (ValueError, TypeError):
                            formatted_value = str(raw_value)
                else:
                    formatted_value = "N/A"
            else:
                # Ricerca flessibile
                found = False
                for df_col in display_df.columns:
                    if col.lower() == df_col.lower():
                        raw_value = latest[df_col]
                        if pd.notna(raw_value):
                            if isinstance(raw_value, (int, float)):
                                formatted_value = f"${raw_value/1e6:.2f}M"
                            else:
                                try:
                                    num_value = float(raw_value)
                                    formatted_value = f"${num_value/1e6:.2f}M"
                                except (ValueError, TypeError):
                                    formatted_value = str(raw_value)
                        else:
                            formatted_value = "N/A"
                        found = True
                        break
                
                if not found:
                    formatted_value = "N/A"
        except Exception as e:
            formatted_value = "N/A"
        
        results[i] = {"col": col, "value": formatted_value}
    
    return results

def streamlit_mapping_complex(df, mapping_config):
    """
    Versione migliorata che mostra i valori per aiutare nella selezione delle colonne
    """
    new_mapping = {}
    
    st.subheader("Mapping Interattivo (Income Statement)")
    
    # Ottieni i dati trimestrali, se disponibili
    quarterly_df = st.session_state.quarterly_data if 'quarterly_data' in st.session_state else None
    
    with st.expander("Colonne disponibili nell'income statement", expanded=True):
        # Determina quale DataFrame usare per visualizzare i valori
        display_df = quarterly_df if quarterly_df is not None else df
        latest_values = display_df.iloc[0] if not display_df.empty else pd.Series()
        
        # Crea una tabella per visualizzare tutte le colonne con i loro valori
        cols_data = []
        for i, col in enumerate(df.columns, start=1):
            try:
                # Verifica se la colonna esiste anche nei dati trimestrali
                if quarterly_df is not None and col in quarterly_df.columns:
                    raw_value = latest_values[col]
                else:
                    # Fallback ai dati annuali se la colonna non esiste nei trimestrali
                    raw_value = df.iloc[0][col] if col in df.columns else None
                
                # Formatta il valore
                if pd.isna(raw_value):
                    formatted_value = "N/A"
                elif isinstance(raw_value, (int, float)):
                    formatted_value = f"${raw_value/1e6:.2f}M"
                else:
                    try:
                        num_value = float(raw_value)
                        formatted_value = f"${num_value/1e6:.2f}M"
                    except (ValueError, TypeError):
                        formatted_value = str(raw_value)
            except Exception:
                formatted_value = "N/A"
            
            cols_data.append({
                "Indice": i,
                "Colonna": col,
                "Valore Ultimo Periodo": formatted_value
            })
        
        cols_df = pd.DataFrame(cols_data)
        st.dataframe(cols_df, hide_index=True)
        
        # Indica la fonte dei dati per migliore comprensione
        source = "trimestre" if quarterly_df is not None else "anno"
        st.info(f"I valori mostrati sono dell'ultimo {source} disponibile")
    
    for target, candidates in mapping_config.items():
        available = [cand for cand in candidates if cand in df.columns]
        
        st.write(f"### Mapping per '{target}'")
        
        if not available:
            st.warning(f"Nessuna delle candidate predefinite è stata trovata. Verrà usato l'intero elenco disponibile.")
            available = list(df.columns)
            candidates_info = display_candidates_with_values(df, available, quarterly_df)
            default_value = available[0] if available else None
        else:
            st.success(f"Candidate trovate: {', '.join(available)}")
            candidates_info = display_candidates_with_values(df, available, quarterly_df)
            default_value = available[0] if available else None
        
        # Chiavi univoche per ogni input
        target_key = f"mapping_{target}"
        method_key = f"method_{target}"
        select_key = f"select_{target}"
        expr_key = f"expr_{target}"
        
        if method_key not in st.session_state:
            st.session_state[method_key] = "Usa prima opzione disponibile"
        if select_key not in st.session_state:
            st.session_state[select_key] = default_value
        if expr_key not in st.session_state:
            st.session_state[expr_key] = ""
        
        mapping_method = st.radio(
            f"Scegli il metodo di mapping per '{target}':",
            ["Usa prima opzione disponibile", "Seleziona da lista", "Espressione personalizzata"],
            key=method_key
        )
        
        if mapping_method == "Usa prima opzione disponibile":
            if default_value:
                new_mapping[target] = default_value
                # Mostra anche il valore dell'opzione selezionata
                default_value_idx = available.index(default_value) + 1
                st.info(f"Verrà usato: {default_value} ({candidates_info[default_value_idx]['value']})")
            else:
                st.error("Nessuna opzione disponibile")
                new_mapping[target] = None
        
        elif mapping_method == "Seleziona da lista":
            if available:
                # Crea una lista di opzioni con i valori inclusi
                options_with_values = [f"{col} ({candidates_info[i+1]['value']})" for i, col in enumerate(available)]
                selected_index = 0
                
                if select_key in st.session_state and st.session_state[select_key] in available:
                    selected_index = available.index(st.session_state[select_key])
                
                selected_option_with_value = st.selectbox(
                    f"Seleziona l'opzione per '{target}':",
                    options_with_values,
                    index=selected_index,
                    key=f"{select_key}_with_value"
                )
                
                # Estrai il nome della colonna dal testo selezionato
                selected_option = selected_option_with_value.split(" (")[0]
                st.session_state[select_key] = selected_option
                new_mapping[target] = selected_option
            else:
                st.error("Nessuna opzione disponibile")
                new_mapping[target] = None
        
        elif mapping_method == "Espressione personalizzata":
            st.write("Opzioni disponibili per l'espressione:")
            
            # Crea la tabella delle opzioni con i valori
            options_data = []
            for i, col in enumerate(available, start=1):
                options_data.append({
                    "Indice": i,
                    "Colonna": col,
                    "Valore Ultimo Periodo": candidates_info[i]["value"]
                })
            
            options_df = pd.DataFrame(options_data)
            st.dataframe(options_df, hide_index=True)
            
            st.info("Puoi inserire un singolo numero (es. '1') per selezionare direttamente una colonna, oppure un'espressione matematica usando gli indici (es. '1+2-3').")
            
            expr_input = st.text_input(
                f"Inserisci un'espressione per '{target}':",
                key=expr_key
            )
            
            if expr_input:
                # Se l'input è un singolo numero, seleziona la colonna corrispondente
                if expr_input.strip().isdigit():
                    idx = int(expr_input.strip())
                    if 1 <= idx <= len(available):
                        new_mapping[target] = available[idx-1]
                        st.info(f"Colonna selezionata: {available[idx-1]} ({candidates_info[idx]['value']})")
                    else:
                        st.error(f"Indice fuori range. Inserisci un numero tra 1 e {len(available)}.")
                        if default_value:
                            new_mapping[target] = default_value
                            default_value_idx = available.index(default_value) + 1
                            st.info(f"Verrà usato il default: {default_value} ({candidates_info[default_value_idx]['value']})")
                        else:
                            new_mapping[target] = None
                # Se è un'espressione aritmetica
                elif any(op in expr_input for op in ['+', '-', '*', '/']):
                    transformed = transform_expr(expr_input, available)
                    new_mapping[target] = transformed
                    st.info(f"Espressione trasformata: {transformed}")
                    
                    # Calcola il valore dell'espressione utilizzando i dati trimestrali se disponibili
                    try:
                        # Scegli quale DataFrame usare per calcolare l'anteprima
                        calc_df = quarterly_df if quarterly_df is not None else df
                        latest_row = {col: float(calc_df.iloc[0][col]) if col in calc_df.iloc[0] and pd.notna(calc_df.iloc[0][col]) else 0 
                                     for col in calc_df.columns}
                        
                        # Sostituisci i nomi di colonna con i valori
                        expr_with_values = transformed
                        for col in calc_df.columns:
                            if f"`{col}`" in expr_with_values:
                                value = latest_row.get(col, 0)
                                expr_with_values = expr_with_values.replace(f"`{col}`", str(value))
                        
                        # Valuta l'espressione
                        result = eval(expr_with_values)
                        period_type = "trimestre" if quarterly_df is not None else "anno"
                        st.success(f"Valore calcolato (ultimo {period_type}): ${result/1e6:.2f}M")
                    except Exception as e:
                        st.warning(f"Non è possibile calcolare il valore dell'espressione: {e}")
                else:
                    # Potrebbe essere un nome di colonna diretto
                    if expr_input in df.columns:
                        new_mapping[target] = expr_input
                        
                        # Ottieni il valore dai dati trimestrali se disponibili
                        if quarterly_df is not None and expr_input in quarterly_df.columns:
                            value = float(quarterly_df.iloc[0][expr_input]) if pd.notna(quarterly_df.iloc[0][expr_input]) else None
                        else:
                            value = float(df.iloc[0][expr_input]) if pd.notna(df.iloc[0][expr_input]) else None
                            
                        formatted_value = f"${value/1e6:.2f}M" if value is not None else "N/A"
                        period_type = "trimestre" if quarterly_df is not None and expr_input in quarterly_df.columns else "anno"
                        st.info(f"Colonna selezionata direttamente: {expr_input} ({formatted_value}, ultimo {period_type})")
                    else:
                        st.error(f"Input non valido. Inserisci un indice, un'espressione aritmetica o un nome di colonna valido.")
                        if default_value:
                            new_mapping[target] = default_value
                            default_value_idx = available.index(default_value) + 1
                            st.info(f"Verrà usato il default: {default_value} ({candidates_info[default_value_idx]['value']})")
                        else:
                            new_mapping[target] = None
            else:
                if default_value:
                    new_mapping[target] = default_value
                    default_value_idx = available.index(default_value) + 1
                    st.info(f"Nessuna espressione inserita. Verrà usato il default: {default_value} ({candidates_info[default_value_idx]['value']})")
                else:
                    new_mapping[target] = None
        
        st.markdown("---")
    
    return new_mapping


def evaluate_mapping_latest(df, mapping_dict):
    """
    Valuta l'espressione (eventualmente aritmetica) definita per ciascuna voce sul record più recente.
    """
    latest = df.iloc[0]
    mapped = {}
    for target, expr in mapping_dict.items():
        if expr is None:
            mapped[target] = None
        else:
            if any(op in expr for op in ['+', '-', '*', '/']) and '`' not in expr:
                expr = transform_expr(expr, list(df.columns))
            if any(op in expr for op in ['+', '-', '*', '/']):
                try:
                    def replace_col(match):
                        colname = match.group(0).strip('`')
                        try:
                            val = float(latest[colname])
                            if pd.isna(val) or str(val).lower() == "nan":
                                return "0"
                            return str(val)
                        except Exception:
                            return "0"
                    transformed_expr = re.sub(r'`[^`]+`', replace_col, expr)
                    result = eval(transformed_expr)
                    mapped[target] = result
                except Exception as e:
                    st.error(f"Errore nell'eval per {target} con '{expr}': {e}")
                    mapped[target] = None
            else:
                if expr in latest.index:
                    try:
                        mapped[target] = float(latest[expr])
                    except Exception:
                        mapped[target] = None
                else:
                    mapped[target] = None
    return mapped

def compute_income_mapping_timeseries(df, mapping_dict):
    results = {}
    for idx, row in df.iterrows():
        temp_df = pd.DataFrame([row], index=[idx])
        mapped = evaluate_mapping_latest(temp_df, mapping_dict)
        results[idx] = mapped
    return pd.DataFrame.from_dict(results, orient='index')

# Add caching for API calls with longer TTL
@st.cache_data(ttl=7200)  # Cache for 2 hours
def get_company_info(ticker):
    """Fetch company info with caching"""
    if st.session_state.demo_mode:
        return get_demo_company_info(ticker)
    
    try:
        company = yf.Ticker(ticker)
        time.sleep(1)  # Add delay to avoid rate limiting
        info = company.info
        
        # Check if we got a valid response
        if not info or len(info) < 5:  # Basic validity check
            st.warning(f"Risposta limitata da Yahoo Finance per {ticker}. Alcuni dati potrebbero mancare.")
            
        return info
    except Exception as e:
        if "Rate limited" in str(e) or "Too Many Requests" in str(e):
            st.warning("API rata limitata. Passaggio alla modalità demo.")
            st.session_state.demo_mode = True
            return get_demo_company_info(ticker)
        else:
            st.error(f"Errore nel recupero delle informazioni aziendali: {str(e)}")
            return None

@st.cache_data(ttl=7200)  # Cache for 2 hours
def get_financial_data(ticker):
    """Fetch financial statements with caching"""
    if st.session_state.demo_mode:
        demo_data = get_demo_financial_data(ticker)
        
        # Convert demo data to pandas DataFrame format
        fin_data = pd.DataFrame(demo_data["financials"])
        fin_data.index = pd.to_datetime(demo_data["dates"])
        
        # Transpose to match yfinance format
        fin_data = fin_data.T
        
        return fin_data
    
    try:
        company = yf.Ticker(ticker)
        time.sleep(1)  # Add delay to avoid rate limiting
        financials = company.financials
        
        if financials is None or financials.empty:
            st.warning(f"Nessun dato finanziario disponibile per {ticker}. Passaggio alla modalità demo.")
            st.session_state.demo_mode = True
            return get_financial_data(ticker)  # Recursively call with demo mode activated
            
        return financials
    except Exception as e:
        if "Rate limited" in str(e) or "Too Many Requests" in str(e):
            st.warning("API rata limitata. Passaggio alla modalità demo.")
            st.session_state.demo_mode = True
            return get_financial_data(ticker)  # Recursively call with demo mode activated
        else:
            st.error(f"Errore nel recupero dei dati finanziari: {str(e)}")
            return None

def load_ticker_data():
    ticker = st.session_state.ticker
    try:
        with st.spinner(f"Caricamento dati per {ticker}..."):
            # Get financial data (it will use demo data if in demo mode)
            financials = get_financial_data(ticker)
            
            if financials is None:
                st.error(f"Nessun dato finanziario disponibile per {ticker}")
                return None
            
            # Transform to match the expected format
            annual_income_statement = financials.T.sort_index(ascending=False)
            
            if annual_income_statement.empty:
                st.error(f"Nessun dato finanziario trovato per {ticker}")
                return None
            
            st.success(f"Dati caricati con successo per {ticker}")
            return annual_income_statement
    except Exception as e:
        st.error(f"Errore durante il caricamento dei dati: {e}")
        return None

def format_dataframe(df):
    """Format dataframe for display"""
    if df is None or df.empty:
        return df
    
    # Copy to avoid modifying the original
    formatted_df = df.copy()
    
    # Format percentage columns
    percent_columns = ["Gross Margin", "Revenue Y/Y", "Net Income Y/Y", "Tax Percentage", "Net Margin", "Operating Margin"]
    for col in percent_columns:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(
                lambda x: f"{x:.2f}%" if pd.notna(x) and not isinstance(x, str) else x
            )
    
    # Format monetary columns
    amount_columns = ["Revenue", "Total COGS", "Gross Profit", "SG&A", "R&D",
                      "Operating Income", "Pretax Income", "Taxes", "Net Income", "Net Interest Income"]
    for col in amount_columns:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(
                lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A"
            )
    
    # Format EPS
    if "EPS" in formatted_df.columns:
        formatted_df["EPS"] = formatted_df["EPS"].apply(
            lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
        )
    
    return formatted_df

def save_ticker_input():
    st.session_state.ticker = st.session_state.ticker_input.strip().upper()
    st.session_state.step = 'load_data'
    st.session_state.annual_income_statement = None
    st.session_state.income_mapping_user = None

def save_mapping():
    st.session_state.income_mapping_user = streamlit_mapping_complex(
        st.session_state.annual_income_statement, 
        config["income_mapping"]
    )
    st.session_state.step = 'analyze'

def perform_analysis():
    with st.spinner("Elaborazione dati in corso..."):
        annual_income_statement = st.session_state.annual_income_statement
        income_mapping_user = st.session_state.income_mapping_user

        # Calcolo del mapping per tutte le righe (timeseries)
        df_income_ts = compute_income_mapping_timeseries(annual_income_statement, income_mapping_user)

        # Aggiustamento per 'Gross Profit': se non è stato mappato, lo calcola come Revenue - Total COGS
        for idx in df_income_ts.index:
            if (df_income_ts.at[idx, "Gross Profit"] is None or pd.isna(df_income_ts.at[idx, "Gross Profit"])) \
               and pd.notnull(df_income_ts.at[idx, "Revenue"]) and pd.notnull(df_income_ts.at[idx, "Total COGS"]):
                df_income_ts.at[idx, "Gross Profit"] = df_income_ts.at[idx, "Revenue"] - df_income_ts.at[idx, "Total COGS"]

        # Calcolo dei costi operativi e degli aggiustamenti per Operating Income e Taxes
        for idx in df_income_ts.index:
            sg_a = df_income_ts.at[idx, "SG&A"] if pd.notnull(df_income_ts.at[idx, "SG&A"]) else 0
            r_and_d = df_income_ts.at[idx, "R&D"] if pd.notnull(df_income_ts.at[idx, "R&D"]) else 0
            s_and_m = df_income_ts.at[idx, "S&M"] if pd.notnull(df_income_ts.at[idx, "S&M"]) else 0
            df_income_ts.at[idx, "Operating Expenses"] = sg_a + r_and_d + s_and_m
            if (df_income_ts.at[idx, "Operating Income"] is None or pd.isna(df_income_ts.at[idx, "Operating Income"])) \
               and pd.notnull(df_income_ts.at[idx, "Gross Profit"]):
                df_income_ts.at[idx, "Operating Income"] = df_income_ts.at[idx, "Gross Profit"] - df_income_ts.at[idx, "Operating Expenses"]
            if (df_income_ts.at[idx, "Taxes"] is None or pd.isna(df_income_ts.at[idx, "Taxes"])) \
               and pd.notnull(df_income_ts.at[idx, "Pretax Income"]) and pd.notnull(df_income_ts.at[idx, "Net Income"]):
                df_income_ts.at[idx, "Taxes"] = df_income_ts.at[idx, "Pretax Income"] - df_income_ts.at[idx, "Net Income"]

        # Creazione della riga TTM a partire dai dati trimestrali se non siamo in demo mode
        if not st.session_state.demo_mode:
            try:
                company = yf.Ticker(st.session_state.ticker)
                q_financials = company.quarterly_financials
                if q_financials is not None and not q_financials.empty:
                    ttm_series = q_financials.iloc[:, :4].sum(axis=1)
                    ttm_df_temp = pd.DataFrame([ttm_series])
                    ttm_mapped = evaluate_mapping_latest(ttm_df_temp, income_mapping_user)

                    # Aggiustamento per TTM: se 'Gross Profit' non è disponibile, lo calcola come Revenue - Total COGS
                    if (ttm_mapped.get("Gross Profit") is None or pd.isna(ttm_mapped.get("Gross Profit"))) and \
                       (ttm_mapped.get("Revenue") is not None and ttm_mapped.get("Total COGS") is not None):
                        ttm_mapped["Gross Profit"] = ttm_mapped["Revenue"] - ttm_mapped["Total COGS"]

                    sg_a = ttm_mapped.get("SG&A", 0)
                    r_and_d = ttm_mapped.get("R&D", 0)
                    s_and_m = ttm_mapped.get("S&M", 0)
                    ttm_mapped["Operating Expenses"] = sg_a + r_and_d + s_and_m
                    if (ttm_mapped.get("Operating Income") is None or pd.isna(ttm_mapped.get("Operating Income"))) and \
                       ttm_mapped.get("Gross Profit") is not None:
                        ttm_mapped["Operating Income"] = ttm_mapped["Gross Profit"] - ttm_mapped["Operating Expenses"]
                    if (ttm_mapped.get("Taxes") is None or pd.isna(ttm_mapped.get("Taxes"))) and \
                       ttm_mapped.get("Pretax Income") is not None and ttm_mapped.get("Net Income") is not None:
                        ttm_mapped["Taxes"] = ttm_mapped["Pretax Income"] - ttm_mapped["Net Income"]

                    # Calcolo del margine lordo per il TTM
                    if ttm_mapped.get("Revenue") and ttm_mapped.get("Revenue") != 0:
                        ttm_mapped["Gross Margin"] = (ttm_mapped["Gross Profit"] / ttm_mapped["Revenue"]) * 100
                    else:
                        ttm_mapped["Gross Margin"] = None
                        ttm_mapped["Net Income Y/Y"] = None
                        ttm_mapped["Revenue Y/Y"] = None

                    # Creazione della riga TTM
                    ttm_df = pd.DataFrame(ttm_mapped, index=["TTM"])

                    # Concatena la riga TTM in cima al timeseries annuale
                    df_income_full = pd.concat([ttm_df, df_income_ts])
                else:
                    st.warning("Dati trimestrali non disponibili. Si utilizzeranno solo i dati annuali.")
                    df_income_full = df_income_ts.copy()
            except Exception as e:
                st.warning(f"Impossibile calcolare TTM: {e}. Si utilizzeranno solo i dati annuali.")
                df_income_full = df_income_ts.copy()
        else:
            # In modalità demo, usa solo i dati annuali
            df_income_full = df_income_ts.copy()

        # Calcolo delle variazioni Y/Y per tutte le righe (escluso temporaneamente TTM)
        df_income_full_sorted = df_income_full.copy()
        if "TTM" in df_income_full_sorted.index:
            regular_years = df_income_full_sorted.drop("TTM")
        else:
            regular_years = df_income_full_sorted

        # Converti l'indice in datetime per garantire l'ordinamento corretto
        regular_years.index = pd.to_datetime(regular_years.index, errors='coerce')

        # Ordina per data dal più vecchio al più recente
        regular_years_sorted = regular_years.sort_index(ascending=True)

        # Calcola le variazioni YoY: pct_change confronta ogni riga con la precedente
        regular_years_sorted["Revenue Y/Y"] = regular_years_sorted["Revenue"].pct_change() * 100
        regular_years_sorted["Net Income Y/Y"] = regular_years_sorted["Net Income"].pct_change() * 100

        # Riordina dal più recente al più vecchio
        regular_years_final = regular_years_sorted.sort_index(ascending=False)

        # Aggiorna il dataframe originale per le righe regolari
        df_income_full.loc[regular_years_final.index, "Revenue Y/Y"] = regular_years_final["Revenue Y/Y"]
        df_income_full.loc[regular_years_final.index, "Net Income Y/Y"] = regular_years_final["Net Income Y/Y"]

        # Calcola le variazioni Y/Y per la riga TTM confrontandola con il primo anno annuale
        if "TTM" in df_income_full.index and len(df_income_full) > 1:
            next_annual = df_income_full.iloc[1]
            if pd.notna(next_annual["Revenue"]) and next_annual["Revenue"] != 0:
                df_income_full.at["TTM", "Revenue Y/Y"] = ((df_income_full.at["TTM", "Revenue"] / next_annual["Revenue"]) - 1) * 100
            else:
                df_income_full.at["TTM", "Revenue Y/Y"] = None
            if pd.notna(next_annual["Net Income"]) and next_annual["Net Income"] != 0:
                df_income_full.at["TTM", "Net Income Y/Y"] = ((df_income_full.at["TTM", "Net Income"] / next_annual["Net Income"]) - 1) * 100
            else:
                df_income_full.at["TTM", "Net Income Y/Y"] = None

        # Calcolo dei margini
        df_income_full["Gross Margin"] = df_income_full.apply(
            lambda row: (row["Gross Profit"] / row["Revenue"] * 100) if pd.notna(row["Revenue"]) and row["Revenue"] != 0 else None,
            axis=1
        )
        df_income_full["Net Margin"] = df_income_full.apply(
            lambda row: (row["Net Income"] / row["Revenue"] * 100) if pd.notna(row["Revenue"]) and row["Revenue"] != 0 else None,
            axis=1
        )
        df_income_full["Operating Margin"] = df_income_full.apply(
            lambda row: (row["Operating Income"] / row["Revenue"] * 100) if pd.notna(row["Revenue"]) and row["Revenue"] != 0 else None,
            axis=1
        )
        df_income_full["Tax Percentage"] = df_income_full.apply(
            lambda row: (row["Taxes"] / row["Pretax Income"] * 100) if pd.notna(row["Pretax Income"]) and row["Pretax Income"] != 0 else None,
            axis=1
        )

        # Riordino delle colonne finali
        desired_columns = [
            "Revenue", "Total COGS", "Gross Profit", "SG&A", "R&D", "Operating Income",
            "Pretax Income", "Taxes", "Tax Percentage", "Net Income", "EPS", "Net Interest Income",
            "Net Margin", "Operating Margin", "Net Income Y/Y", "Revenue Y/Y", "Gross Margin"
        ]
        df_income_full = df_income_full.reindex(columns=[col for col in desired_columns if col in df_income_full.columns])

        # Conversione in MILIONI
        amount_columns = ["Revenue", "Total COGS", "Gross Profit", "SG&A", "R&D",
                          "Operating Income", "Pretax Income", "Taxes", "Net Income", "Net Interest Income"]
        df_income_display = df_income_full.copy()
        for col in amount_columns:
            if col in df_income_display.columns:
                df_income_display[col] = df_income_display[col] / 1e6

        return df_income_full, df_income_display

        

###############################################
# INTERFACCIA UTENTE CON SIDEBAR
###############################################

# Add demo mode toggle in sidebar
with st.sidebar:
    st.title("Impostazioni")
    demo_toggle = st.checkbox("Usa modalità demo", value=st.session_state.demo_mode, 
                             help="Utilizza dati di esempio invece di dati live. Utile quando l'API è limitata.")
    
    if demo_toggle != st.session_state.demo_mode:
        st.session_state.demo_mode = demo_toggle
        st.experimental_rerun()
    
    if st.session_state.demo_mode:
        st.success("Modalità demo attiva! I dati visualizzati sono di esempio.")
    
    st.markdown("---")
    st.markdown("""
    ### Informazioni
    Questo strumento analizza l'Income Statement di aziende quotate.
    Se ricevi errori di rate limiting, attiva la modalità demo.
    """)

# STEP 1: Input iniziale
if st.session_state.step == 'input':
    st.header("Inserisci il ticker azionario")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input("Ticker (es. AAPL):", value="AAPL", key="ticker_input")
    with col2:
        st.button("Analizza", on_click=save_ticker_input)

# STEP 2: Caricamento dati
elif st.session_state.step == 'load_data':
    annual_income_statement = load_ticker_data()
    
    if annual_income_statement is not None:
        st.session_state.annual_income_statement = annual_income_statement
        st.session_state.step = 'mapping'
        st.rerun()

# STEP 3: Configurazione del mapping
elif st.session_state.step == 'mapping':
    st.header(f"Configurazione del mapping per {st.session_state.ticker}")
    
    # Display company info
    info = get_company_info(st.session_state.ticker)
    if info:
        col1, col2 = st.columns([1, 3])
        with col1:
            if "logo_url" in info and info["logo_url"]:
                st.image(info["logo_url"], width=100)
            else:
                st.markdown("🏢")
        with col2:
            st.subheader(info.get("longName", st.session_state.ticker))
            st.markdown(f"**Settore:** {info.get('sector', 'N/A')} | **Industria:** {info.get('industry', 'N/A')}")
            st.markdown(f"**Prezzo attuale:** ${info.get('currentPrice', 'N/A')} | **Market Cap:** ${info.get('marketCap', 0)/1e9:.2f}B")
    
    st.subheader("Record più recente dell'Income Statement Annuale")
    st.dataframe(pd.DataFrame(st.session_state.annual_income_statement.iloc[0]).T)
    
    if st.button("Configura mapping"):
        st.session_state.step = 'mapping_config'
        st.rerun()

# STEP 4: Configurazione del mapping dettagliata
elif st.session_state.step == 'mapping_config':
    st.header(f"Mappatura dettagliata per {st.session_state.ticker}")
    
    mapping_result = streamlit_mapping_complex(
        st.session_state.annual_income_statement, 
        config["income_mapping"]
    )
    
    if st.button("Applica mapping e procedi con l'analisi"):
        st.session_state.income_mapping_user = mapping_result
        st.session_state.step = 'analyze'
        st.rerun()

# STEP 5: Analisi
elif st.session_state.step == 'analyze':
    st.header(f"Analisi Income Statement per {st.session_state.ticker}")
    
    # Display company info
    info = get_company_info(st.session_state.ticker)
    if info:
        col1, col2 = st.columns([1, 3])
        with col1:
            if "logo_url" in info and info["logo_url"]:
                st.image(info["logo_url"], width=100)
            else:
                st.markdown("🏢")
        with col2:
            st.subheader(info.get("longName", st.session_state.ticker))
            st.markdown(f"**Settore:** {info.get('sector', 'N/A')} | **Industria:** {info.get('industry', 'N/A')}")
            st.markdown(f"**Prezzo attuale:** ${info.get('currentPrice', 'N/A')} | **Market Cap:** ${info.get('marketCap', 0)/1e9:.2f}B")
    
    if st.session_state.demo_mode:
        st.info("⚠️ Visualizzando dati demo. I dati potrebbero non essere aggiornati.")
    
    try:
        df_income_full, df_income_display = perform_analysis()
        
        st.subheader("Income Statement Finale (valori in milioni)")
        st.dataframe(format_dataframe(df_income_display), use_container_width=True)
        
        # Visualizzazioni aggiuntive con Plotly
        st.subheader("Analisi Grafica")
        
        if "TTM" in df_income_full.index:
            chart_data = df_income_full.drop("TTM")
        else:
            chart_data = df_income_full.copy()
        
        fig1, fig2, fig3 = create_charts(chart_data)
        
        tab1, tab2, tab3 = st.tabs(["Revenue & Net Income", "Margini di Profitto", "Crescita YoY"])
        
        with tab1:
            st.plotly_chart(fig1, use_container_width=True)
        with tab2:
            st.plotly_chart(fig2, use_container_width=True)
        with tab3:
            st.plotly_chart(fig3, use_container_width=True)
        
        # Show key metrics if we have at least one row of data
        if len(df_income_full) > 0:
            st.subheader("Metriche Chiave")
            latest_data = df_income_full.iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                revenue_yoy = latest_data["Revenue Y/Y"] if "Revenue Y/Y" in latest_data and pd.notna(latest_data["Revenue Y/Y"]) else 0
                st.metric(
                    "Crescita Ricavi (YoY)", 
                    f"{revenue_yoy:.2f}%", 
                    delta=f"{revenue_yoy:.2f}%"
                )
            
            with col2:
                net_income_yoy = latest_data["Net Income Y/Y"] if "Net Income Y/Y" in latest_data and pd.notna(latest_data["Net Income Y/Y"]) else 0
                st.metric(
                    "Crescita Utile Netto (YoY)", 
                    f"{net_income_yoy:.2f}%", 
                    delta=f"{net_income_yoy:.2f}%"
                )
            
            with col3:
                gross_margin = latest_data["Gross Margin"] if "Gross Margin" in latest_data and pd.notna(latest_data["Gross Margin"]) else 0
                if isinstance(gross_margin, str):
                    gross_margin = float(gross_margin.strip('%'))
                st.metric("Margine Lordo", f"{gross_margin:.2f}%")
            
            with col4:
                net_margin = latest_data["Net Margin"] if "Net Margin" in latest_data and pd.notna(latest_data["Net Margin"]) else 0
                if isinstance(net_margin, str):
                    net_margin = float(net_margin.strip('%'))
                st.metric("Margine Netto", f"{net_margin:.2f}%")
        
        # Opzione per scaricare i dati
        csv = format_dataframe(df_income_display).to_csv().encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f'{st.session_state.ticker}_income_statement_analysis.csv',
            mime='text/csv',
        )
        
        if st.button("Ricomincia con un nuovo ticker"):
            st.session_state.step = 'input'
            st.rerun()
            
    except Exception as e:
        st.error(f"Errore durante l'analisi: {e}")
        st.exception(e)
        if st.button("Torna all'inizio"):
            st.session_state.step = 'input'
            st.rerun()

# Footer
st.markdown("---")
st.markdown("Creato con ❤️ usando Streamlit e yfinance")