import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas_ta as ta

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="주식 분석 대시보드 by Gemini", layout="wide", initial_sidebar_state="expanded")

# --- Helper Functions (데이터 가져오기 등) ---
@st.cache_data(ttl=3600) # 데이터 캐싱 (1시간 동안 유지)
def get_stock_data(ticker_symbol, period="1y"):
    """yfinance를 사용하여 주식 데이터를 가져옵니다."""
    stock = yf.Ticker(ticker_symbol)
    hist_data = stock.history(period=period)
    info = stock.info
    financials = stock.financials 
    balance_sheet = stock.balance_sheet 
    cashflow = stock.cashflow 
    return hist_data, info if info else {}, financials, balance_sheet, cashflow

def calculate_technical_indicators(df, sma_short_visible, sma_short_val, sma_long_visible, sma_long_val, 
                                   rsi_visible, rsi_window_val, 
                                   macd_visible, macd_fast_val, macd_slow_val, macd_signal_val):
    """기술적 분석 지표를 계산합니다."""
    df_ta = df.copy() 
    if sma_short_visible: 
        df_ta[f'SMA_{sma_short_val}'] = ta.sma(df_ta["Close"], length=sma_short_val)
    if sma_long_visible:
        df_ta[f'SMA_{sma_long_val}'] = ta.sma(df_ta["Close"], length=sma_long_val)
    
    if rsi_visible: 
        df_ta['RSI'] = ta.rsi(df_ta["Close"], length=rsi_window_val)

    if macd_visible: 
        macd_df = ta.macd(df_ta["Close"], fast=macd_fast_val, slow=macd_slow_val, signal=macd_signal_val)
        if macd_df is not None and not macd_df.empty:
            macd_df.columns = [f"{col.split('_')[0]}_{macd_fast_val}_{macd_slow_val}_{macd_signal_val}" if '_' in col else f"{col}_{macd_fast_val}_{macd_slow_val}_{macd_signal_val}" for col in macd_df.columns]
            df_ta = df_ta.join(macd_df)
    return df_ta

# --- 사이드바 UI 구성 ---
st.sidebar.image("https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png", width=100) 
st.sidebar.title("📈 주식 분석 설정")
st.sidebar.markdown("---")

default_ticker = "AAPL" 
ticker_symbol_input = st.sidebar.text_input("분석할 미국 주식 티커 입력:", value=default_ticker, help="예: AAPL, MSFT, GOOGL, NVDA, TSLA").upper()

data_period_options = ["3mo", "6mo", "1y", "2y", "5y", "max"]
selected_period_selectbox = st.sidebar.selectbox("차트 기간:", data_period_options, index=2, help="차트에 표시할 주가 데이터 기간을 선택합니다.")

st.sidebar.subheader("기술적 지표")
show_sma_checkbox_ui = st.sidebar.checkbox("단순 이동평균선 (SMA)", value=True)
sma_short_window_slider_ui = st.sidebar.slider("SMA 단기", 5, 50, 20, help="단기 이동평균선 기간(일)", disabled=not show_sma_checkbox_ui)
sma_long_window_slider_ui = st.sidebar.slider("SMA 장기", 20, 200, 60, help="장기 이동평균선 기간(일)", disabled=not show_sma_checkbox_ui)

show_rsi_checkbox_ui = st.sidebar.checkbox("RSI (상대강도지수)", value=True)
rsi_window_slider_ui = st.sidebar.slider("RSI 기간", 7, 30, 14, disabled=not show_rsi_checkbox_ui)

show_macd_checkbox_ui = st.sidebar.checkbox("MACD", value=True)
macd_fast_slider_ui = st.sidebar.slider("MACD Fast", 5, 50, 12, disabled=not show_macd_checkbox_ui)
macd_slow_slider_ui = st.sidebar.slider("MACD Slow", 10, 100, 26, disabled=not show_macd_checkbox_ui)
macd_signal_slider_ui = st.sidebar.slider("MACD Signal", 5, 50, 9, disabled=not show_macd_checkbox_ui)

st.sidebar.markdown("---")
analyze_button_ui = st.sidebar.button("🚀 분석 시작!", use_container_width=True, type="primary")
st.sidebar.markdown(f"<p style='font-size:0.8em; color:grey;'>데이터 제공: Yahoo Finance (yfinance)</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='font-size:0.8em; color:grey;'>현재시간(KST): {pd.Timestamp.now(tz='Asia/Seoul').strftime('%Y-%m-%d %H:%M')}</p>", unsafe_allow_html=True)


# --- 메인 대시보드 UI 구성 ---
st.title(f"📊 {ticker_symbol_input} 주식 분석 리포트") 
st.markdown("<sub>이 앱은 Gemini의 도움을 받아 제작되었습니다.</sub>", unsafe_allow_html=True)
st.markdown("---")

if analyze_button_ui and ticker_symbol_input:
    with st.spinner(f"{ticker_symbol_input} 데이터를 가져오고 분석하는 중입니다... 잠시만 기다려주세요..."):
        try: # 여기가 try 블록의 시작입니다. (들여쓰기 레벨 1)
            hist_data_raw, info, financials, balance_sheet, cashflow = get_stock_data(ticker_symbol_input, selected_period_selectbox) # 들여쓰기 레벨 2

            if info is None or not info: 
                st.error(f"'{ticker_symbol_input}'에 대한 회사 정보를 가져올 수 없습니다. 티커를 확인해주세요.") # 들여쓰기 레벨 3
            elif hist_data_raw.empty:
                st.error(f"'{ticker_symbol_input}'에 대한 주가 데이터를 가져올 수 없습니다. 티커를 확인해주세요.") # 들여쓰기 레벨 3
            else: # 들여쓰기 레벨 2
                # 회사 정보 표시
                st.subheader(f"🏢 {info.get('longName', ticker_symbol_input)} ( {ticker_symbol_input} ) 회사 개요") # 들여쓰기 레벨 3
                
                sum_col1, sum_col2 = st.columns([0.7, 0.3]) 
                with sum_col1:
                    st.markdown(f"""
                    * **섹터:** {info.get('sector', 'N/A')}
                    * **산업:** {info.get('industry', 'N/A')}
                    * **웹사이트:** <a href='{info.get('website', '#')}' target='_blank'>{info.get('website', 'N/A')}</a>
                    * **직원 수:** {info.get('fullTimeEmployees', 'N/A'):,} 명
                    """, unsafe_allow_html=True) # 들여쓰기 레벨 4 (markdown 내부)
                with sum_col2:
                    current_price_val = info.get('currentPrice', info.get('previousClose')) 
                    market_cap_val = info.get('marketCap')
                    
                    st.metric(label="현재가 (USD)", value=f"{current_price_val:.2f}" if isinstance(current_price_val, (int,float)) else "N/A" )
                    
                    if market_cap_val and isinstance(market_cap_val, (int, float)):
                        if market_cap_val >= 1e12 : 
                            st.metric(label="시가총액 (USD)", value=f"{market_cap_val/1e12:.2f}T") 
                        elif market_cap_val >= 1e9: 
                            st.metric(label="시가총액 (USD)", value=f"{market_cap_val/1e9:.2f}B") 
                        elif market_cap_val > 0:
                            st.metric(label="시가총액 (USD)", value=f"{market_cap_val/1e6:.2f}M") 
                        else:
                            st.metric(label="시가총액 (USD)", value="N/A")
                    else:
                        st.metric(label="시가총액 (USD)", value="N/A")

                with st.expander("자세한 회사 소개 (영문)", expanded=False): # 들여쓰기 레벨 3
                    business_summary_val = info.get('longBusinessSummary')
                    if not business_summary_val or business_summary_val == '제공된 정보 없음.':
                         st.info('제공된 회사 소개 정보가 없습니다.') # 들여쓰기 레벨 4
                    else:
                        st.markdown(f"<div style='height:200px;overflow-y:scroll;padding:10px;border:1px solid #e6e6e6;'>{business_summary_val}</div>", unsafe_allow_html=True) # 들여쓰기 레벨 4
                st.markdown("---") # 들여쓰기 레벨 3

                hist_data_ta = calculate_technical_indicators( # 들여쓰기 레벨 3
                    hist_data_raw.copy(), 
                    show_sma_checkbox_ui, sma_short_window_slider_ui, 
                    show_sma_checkbox_ui, sma_long_window_slider_ui, 
                    show_rsi_checkbox_ui, rsi_window_slider_ui,
                    show_macd_checkbox_ui, macd_fast_slider_ui, macd_slow_slider_ui, macd_signal_slider_ui
                )

                st.subheader("📈 주가 및 기술적 지표") # 들여쓰기 레벨 3
                
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.04, row_heights=[0.55, 0.2, 0.25]) 

                fig.add_trace(go.Candlestick(x=hist_data_ta.index,
                                            open=hist_data_ta['Open'], high=hist_data_ta['High'],
                                            low=hist_data_ta['Low'], close=hist_data_ta['Close'],
                                            name='캔들스틱'), row=1, col=1)
                if show_sma_checkbox_ui: 
                    if f'SMA_{sma_short_window_slider_ui}' in hist_data_ta.columns:
                        fig.add_trace(go.Scatter(x=hist_data_ta.index, y=hist_data_ta[f'SMA_{sma_short_window_slider_ui}'], 
                                                mode='lines', name=f'SMA {sma_short_window_slider_ui}', line=dict(color='orange')), row=1, col=1)
                    if f'SMA_{sma_long_window_slider_ui}' in hist_data_ta.columns:
                        fig.add_trace(go.Scatter(x=hist_data_ta.index, y=hist_data_ta[f'SMA_{sma_long_window_slider_ui}'], 
                                                mode='lines', name=f'SMA {sma_long_window_slider_ui}', line=dict(color='purple')), row=1, col=1)
                
                fig.add_trace(go.Bar(x=hist_data_ta.index, y=hist_data_ta['Volume'], name='거래량', marker_color='rgba(180,180,200,0.5)'), secondary_y=True, row=1, col=1)
                fig.update_layout(
                    yaxis1_title="가격 (USD)", 
                    yaxis2=dict(title='거래량', overlaying='y', side='right', showgrid=False, range=[0, hist_data_ta['Volume'].max()*3.5 if not hist_data_ta['Volume'].empty else 1e6]) 
                )

                if show_rsi_checkbox_ui and 'RSI' in hist_data_ta.columns: # 들여쓰기 레벨 3
                    fig.add_trace(go.Scatter(x=hist_data_ta.index, y=hist_data_ta['RSI'], mode='lines', name='RSI', line=dict(color='green')), row=2, col=1)
                    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="과매수(70)", annotation_position="bottom right", row=2, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="blue", annotation_text="과매도(30)", annotation_position="bottom right", row=2, col=1)
                    fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1) 

                macd_col_base_name = f'_{macd_fast_slider_ui}_{macd_slow_slider_ui}_{macd_signal_slider_ui}' # 들여쓰기 레벨 3
                macd_line_col = f'MACD{macd_col_base_name}'
                macd_signal_col = f'MACDs{macd_col_base_name}'
                macd_hist_col = f'MACDh{macd_col_base_name}'

                if show_macd_checkbox_ui and macd_line_col in hist_data_ta.columns: # 들여쓰기 레벨 3
                    fig.add_trace(go.Scatter(x=hist_data_ta.index, y=hist_data_ta[macd_line_col], mode='lines', name='MACD', line=dict(color='blue')), row=3, col=1)
                    if macd_signal_col in hist_data_ta.columns:
                         fig.add_trace(go.Scatter(x=hist_data_ta.index, y=hist_data_ta[macd_signal_col], mode='lines', name='Signal', line=dict(color='red')), row=3, col=1)
                    if macd_hist_col in hist_data_ta.columns:
                         fig.add_trace(go.Bar(x=hist_data_ta.index, y=hist_data_ta[macd_hist_col], name='Histogram', marker_color='rgba(100,100,100,0.7)'), row=3, col=1)
                    fig.add_hline(y=0, line_dash="solid", line_color="black", row=3, col=1)
                    fig.update_yaxes(title_text="MACD", row=3, col=1)

                fig.update_layout( # 들여쓰기 레벨 3
                    height=800, 
                    xaxis_rangeslider_visible=False, 
                    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
                    margin=dict(l=20, r=20, t=30, b=20) 
                )
                st.plotly_chart(fig, use_container_width=True) # 들여쓰기 레벨 3
                st.markdown("---") # 들여쓰기 레벨 3

                st.subheader("📑 주요 재무 데이터 (연간, 단위: USD)") # 들여쓰기 레벨 3
                tab1, tab2, tab3 = st.tabs(["손익계산서 (Income Statement)", "대차대조표 (Balance Sheet)", "현금흐름표 (Cash Flow)"]) # 들여쓰기 레벨 3

                def format_financial_table(df): # 들여쓰기 레벨 3
                    if df is None or df.empty: # 들여쓰기 레벨 4
                        return None
                    df_processed = df.iloc[:, :min(4, df.shape[1])].copy()
                    new_columns = []
                    for col in df_processed.columns:
                        if isinstance(col, pd.Timestamp):
                            new_columns.append(col.strftime('%Y'))
                        elif isinstance(col, str) and '-' in col:
                            try:
                                new_columns.append(pd.to_datetime(col).strftime('%Y'))
                            except ValueError:
                                new_columns.append(str(col).split('-')[0]) 
                        else:
                            new_columns.append(str(col))
                    df_processed.columns = new_columns
                    return df_processed.style.format("{:,.0f}", na_rep="-")

                with tab1: # 들여쓰기 레벨 3
                    styled_financials = format_financial_table(financials) # 들여쓰기 레벨 4
                    if styled_financials is not None: 
                        st.dataframe(styled_financials) # 들여쓰기 레벨 5
                    else:
                        st.info(f"{ticker_symbol_input}의 연간 손익계산서 정보를 가져올 수 없습니다.") # 들여쓰기 레벨 5
                with tab2: # 들여쓰기 레벨 3
                    styled_balance_sheet = format_financial_table(balance_sheet) # 들여쓰기 레벨 4
                    if styled_balance_sheet is not None:
                        st.dataframe(styled_balance_sheet) # 들여쓰기 레벨 5
                    else:
                        st.info(f"{ticker_symbol_input}의 연간 대차대조표 정보를 가져올 수 없습니다.") # 들여쓰기 레벨 5
                with tab3: # 들여쓰기 레벨 3
                    styled_cashflow = format_financial_table(cashflow) # 들여쓰기 레벨 4
                    if styled_cashflow is not None:
                        st.dataframe(styled_cashflow) # 들여쓰기 레벨 5
                    else:
                        st.info(f"{ticker_symbol_input}의 연간 현금흐름표 정보를 가져올 수 없습니다.") # 들여쓰기 레벨 5
                st.markdown("---") # 들여쓰기 레벨 3
                
                st.subheader("밸류에이션 참고 (매우 간략화됨)") # 들여쓰기 레벨 3
                val_col1, val_col2 = st.columns(2) # 들여쓰기 레벨 3

                with val_col1: # 들여쓰기 레벨 3
                    st.markdown("##### PER 기반 참고치") # 들여쓰기 레벨 4
                    current_pe_raw_val = info.get('trailingPE')
                    eps_current_raw_val = info.get('trailingEps')
                    
                    if current_pe_raw_val is not None and eps_current_raw_val is not None and isinstance(current_pe_raw_val, (int, float)) and isinstance(eps_current_raw_val, (int, float)): # 들여쓰기 레벨 4
                        st.write(f"현재 PER (TTM): **{current_pe_raw_val:.2f}**") # 들여쓰기 레벨 5
                        st.write(f"현재 EPS (TTM): **${eps_current_raw_val:.2f}**")
                        
                        assumed_pe_default_val = round(float(current_pe_raw_val),1)
                        assumed_pe_val = st.number_input("적용할 목표 PER:", 
                                                     value=assumed_pe_default_val, 
                                                     min_value=1.0, max_value=200.0, step=0.1, key="target_pe_input_val_final_v3", 
                                                     format="%.1f")
                        estimated_price_pe_val = eps_current_raw_val * assumed_pe_val
                        st.success(f"➡️ 목표 PER 적용 시 참고 주가: **${estimated_price_pe_val:.2f}**")
                    else: # 들여쓰기 레벨 4
                        st.warning("PER 또는 EPS 정보가 유효하지 않거나 부족하여 계산할 수 없습니다.") # 들여쓰기 레벨 5

                with val_col2: # 들여쓰기 레벨 3
                    st.markdown("##### PBR 기반 참고치") # 들여쓰기 레벨 4
                    current_pbr_raw_val = info.get('priceToBook')
                    book_value_per_share_calc_val = None
                    
                    if current_price_val and isinstance(current_price_val, (int,float)) and \
                       current_pbr_raw_val and isinstance(current_pbr_raw_val, (int,float)) and current_pbr_raw_val != 0:
                        book_value_per_share_calc_val = current_price_val / current_pbr_raw_val

                    if current_pbr_raw_val and isinstance(current_pbr_raw_val, (int,float)): # 들여쓰기 레벨 4
                        st.write(f"현재 PBR: **{current_pbr_raw_val:.2f}**") # 들여쓰기 레벨 5
                        if book_value_per_share_calc_val and isinstance(book_value_per_share_calc_val, (int,float)):
                            st.write(f"계산된 BPS (주당순자산): **${book_value_per_share_calc_val:.2f}**")
                        
                        assumed_pbr_default_val = round(float(current_pbr_raw_val),1) if book_value_per_share_calc_val else 1.0
                        assumed_pbr_val = st.number_input("적용할 목표 PBR:",
                                                      value=assumed_pbr_default_val,
                                                      min_value=0.1, max_value=50.0, step=0.1, key="target_pbr_input_final_v3", 
                                                      format="%.1f")
                        if book_value_per_share_calc_val and isinstance(book_value_per_share_calc_val, (int,float)): # 들여쓰기 레벨 5
                            estimated_price_pbr_val = book_value_per_share_calc_val * assumed_pbr_val
                            st.success(f"➡️ 목표 PBR 적용 시 참고 주가: **${estimated_price_pbr_val:.2f}**") # 들여쓰기 레벨 6
                        else: # 들여쓰기 레벨 5
                            st.warning("BPS 정보가 부족하여 PBR 기반 추정 주가를 계산할 수 없습니다.") # 들여쓰기 레벨 6
                    else: # 들여쓰기 레벨 4
                        st.warning("PBR 정보가 유효하지 않거나 부족합니다.") # 들여쓰기 레벨 5

                st.info("💡 위 평가는 매우 단순화된 참고용이며, 실제 투자 결정에 사용되어서는 안 됩니다. DCF, RIM 등 더 정교한 모델과 종합적인 분석이 필요합니다. 이 부분은 향후 앱 기능 확장을 통해 개선될 수 있습니다.") # 들여쓰기 레벨 3
        
        except Exception as e: # 여기가 line 281 근처입니다. try와 같은 들여쓰기 레벨(레벨 1)인지 확인!
            st.error(f"'{ticker_symbol_input}' 데이터 처리 중 예상치 못한 오류가 발생했습니다: {str(e)}") # 들여쓰기 레벨 2
            st.error("인터넷 연결을 확인하거나, 티커 심볼이 정확한지 다시 한번 확인해주세요. (예: 미국 주식 AAPL, MSFT, GOOGL)") # 들여쓰기 레벨 2
            st.error("문제가 지속되면 잠시 후 다시 시도해주세요. (데이터 제공처의 일시적인 제한일 수 있습니다.)") # 들여쓰기 레벨 2

elif analyze_button_ui and not ticker_symbol_input: # 이 elif는 맨 처음 if와 같은 들여쓰기 레벨 (레벨 0)
    st.warning("⚠️ 분석할 종목 티커를 사이드바에 입력해주세요.") # 들여쓰기 레벨 1
else: # 이 else도 맨 처음 if와 같은 들여쓰기 레벨 (레벨 0)
    # 초기 화면 안내 메시지
    st.info("👈 사이드바에서 분석할 미국 주식의 티커를 입력하고 '분석 시작!' 버튼을 눌러주세요. 예시 티커: AAPL, MSFT, GOOGL, NVDA, TSLA 등") # 들여쓰기 레벨 1

# --- 앱 정보 및 면책 조항 ---
st.markdown("---")
st.markdown("""
**면책 조항 (Disclaimer)**
* 본 애플리케이션에서 제공하는 모든 정보는 교육적 및 정보 제공 목적으로만 사용되어야 하며, 어떠한 경우에도 투자 조언으로 간주되어서는 안 됩니다.
* 제공되는 데이터는 실제 시장 데이터와 다소 차이가 있거나 지연될 수 있으며, 정보의 정확성, 완전성, 적시성을 보장하지 않습니다.
* 모든 투자 결정은 사용자 본인의 독립적인 판단과 책임 하에 이루어져야 합니다. 본 애플리케이션 사용으로 인해 발생할 수 있는 어떠한 종류의 손실이나 손해에 대해서도 제작자(또는 AI)는 책임을 지지 않습니다.
* 데이터는 주로 `yfinance` 라이브러리를 통해 Yahoo Finance에서 제공하는 정보를 기반으로 하며, 해당 서비스의 약관을 따릅니다.
* 본 애플리케이션은 Google의 생성형 AI(Gemini)의 도움을 받아 구상 및 코드 일부가 작성되었습니다.
""")
