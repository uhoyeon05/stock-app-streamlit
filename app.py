import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas_ta as ta # 기술적 분석 지표용
# import requests # 향후 외부 API 호출용, 초기 버전에서는 직접 사용하지 않음

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="주식 분석 대시보드 by Gemini", layout="wide")

# --- Helper Functions (데이터 가져오기 등) ---
@st.cache_data(ttl=3600) # 데이터 캐싱 (1시간 동안 유지)
def get_stock_data(ticker_symbol, period="1y"):
    """yfinance를 사용하여 주식 데이터를 가져옵니다."""
    stock = yf.Ticker(ticker_symbol)
    hist_data = stock.history(period=period)
    info = stock.info
    financials = stock.financials # 연간 손익계산서
    balance_sheet = stock.balance_sheet # 연간 대차대조표
    cashflow = stock.cashflow # 연간 현금흐름표
    return hist_data, info, financials, balance_sheet, cashflow

def calculate_technical_indicators(df, sma_short_visible, sma_short_val, sma_long_visible, sma_long_val, 
                                   rsi_visible, rsi_window_val, 
                                   macd_visible, macd_fast_val, macd_slow_val, macd_signal_val):
    """기술적 분석 지표를 계산합니다."""
    # 함수 호출 시 UI에서 체크박스 값과 슬라이더 값을 직접 받도록 수정
    if sma_short_visible: 
        df[f'SMA_{sma_short_val}'] = ta.sma(df["Close"], length=sma_short_val)
    if sma_long_visible:
        df[f'SMA_{sma_long_val}'] = ta.sma(df["Close"], length=sma_long_val)
    
    if rsi_visible: 
        df['RSI'] = ta.rsi(df["Close"], length=rsi_window_val)

    if macd_visible: 
        macd_df = ta.macd(df["Close"], fast=macd_fast_val, slow=macd_slow_val, signal=macd_signal_val)
        if macd_df is not None and not macd_df.empty:
             # 컬럼 이름 충돌 방지 및 명확성 위해 접두사/접미사 사용 가능
             macd_df.columns = [f"{col}_{macd_fast_val}_{macd_slow_val}_{macd_signal_val}" for col in macd_df.columns]
             df = df.join(macd_df)
    return df

# --- 사이드바 UI 구성 ---
st.sidebar.image("https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png", width=100) # 예시 로고
st.sidebar.title("📈 주식 분석 설정")
st.sidebar.markdown("---")

default_ticker = "AAPL" 
ticker_symbol = st.sidebar.text_input("분석할 미국 주식 티커 입력:", value=default_ticker, help="예: AAPL, MSFT, GOOGL, NVDA, TSLA").upper()

data_period_options = ["3mo", "6mo", "1y", "2y", "5y", "max"]
selected_period = st.sidebar.selectbox("차트 기간:", data_period_options, index=2, help="차트에 표시할 주가 데이터 기간을 선택합니다.") # 기본 '1y'

st.sidebar.subheader("기술적 지표")
# 각 지표의 표시 여부와 설정값을 독립적으로 관리
show_sma_checkbox = st.sidebar.checkbox("단순 이동평균선 (SMA)", value=True)
sma_short_window_slider = st.sidebar.slider("SMA 단기", 5, 50, 20, help="단기 이동평균선 기간(일)")
sma_long_window_slider = st.sidebar.slider("SMA 장기", 20, 200, 60, help="장기 이동평균선 기간(일)")

show_rsi_checkbox = st.sidebar.checkbox("RSI (상대강도지수)", value=True)
rsi_window_slider = st.sidebar.slider("RSI 기간", 7, 30, 14)

show_macd_checkbox = st.sidebar.checkbox("MACD", value=True)
macd_fast_slider = st.sidebar.slider("MACD Fast", 5, 50, 12)
macd_slow_slider = st.sidebar.slider("MACD Slow", 10, 100, 26)
macd_signal_slider = st.sidebar.slider("MACD Signal", 5, 50, 9)

st.sidebar.markdown("---")
analyze_button = st.sidebar.button("🚀 분석 시작!", use_container_width=True, type="primary")
st.sidebar.markdown(f"<p style='font-size:0.8em; color:grey;'>데이터 제공: Yahoo Finance (yfinance)</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='font-size:0.8em; color:grey;'>현재시간(KST): {pd.Timestamp.now(tz='Asia/Seoul').strftime('%Y-%m-%d %H:%M')}</p>", unsafe_allow_html=True)


# --- 메인 대시보드 UI 구성 ---
st.title(f"📊 {ticker_symbol} 주식 분석 리포트")
st.markdown("<sub>이 앱은 Gemini의 도움을 받아 제작되었습니다.</sub>", unsafe_allow_html=True)
st.markdown("---")

if analyze_button and ticker_symbol:
    with st.spinner(f"{ticker_symbol} 데이터를 가져오고 분석하는 중입니다... 잠시만 기다려주세요..."):
        try:
            hist_data_raw, info, financials, balance_sheet, cashflow = get_stock_data(ticker_symbol, selected_period)

            if hist_data_raw.empty:
                st.error(f"'{ticker_symbol}'에 대한 주가 데이터를 가져올 수 없습니다. 티커를 확인해주세요.")
            else:
                # 회사 정보 표시
                st.subheader(f"🏢 {info.get('longName', ticker_symbol)} ( {ticker_symbol} ) 회사 개요")
                
                sum_col1, sum_col2 = st.columns([0.7, 0.3]) 
                with sum_col1:
                    st.markdown(f"""
                    * **섹터:** {info.get('sector', 'N/A')}
                    * **산업:** {info.get('industry', 'N/A')}
                    * **웹사이트:** [{info.get('website', 'N/A')}]({info.get('website', '#')})
                    * **직원 수:** {info.get('fullTimeEmployees', 'N/A'):,} 명
                    """)
                with sum_col2:
                    current_price = info.get('currentPrice', info.get('previousClose', 'N/A')) # 장중에는 currentPrice, 장마감후에는 previousClose가 더 정확할 수 있음
                    market_cap = info.get('marketCap', 0)
                    
                    st.metric(label="현재가 (USD)", value=f"{current_price:.2f}" if isinstance(current_price, (int,float)) else "N/A" )
                    if market_cap and market_cap > 1e12 : # 조 단위
                        st.metric(label="시가총액 (USD)", value=f"{market_cap/1e12:.2f}T") # Trillion
                    elif market_cap and market_cap > 1e9: # 억 단위
                         st.metric(label="시가총액 (USD)", value=f"{market_cap/1e9:.2f}B") # Billion
                    elif market_cap:
                         st.metric(label="시가총액 (USD)", value=f"{market_cap/1e6:.2f}M") # Million
                    else:
                        st.metric(label="시가총액 (USD)", value="N/A")


                with st.expander("자세한 회사 소개 (영문)", expanded=False):
                    st.write(info.get('longBusinessSummary', '제공된 정보 없음.'))
                st.markdown("---")


                # 기술적 분석 지표 계산 (UI에서 받은 값 사용)
                hist_data_ta = calculate_technical_indicators(
                    hist_data_raw.copy(), 
                    show_sma_checkbox, sma_short_window_slider, 
                    show_sma_checkbox, sma_long_window_slider, # SMA 단기/장기는 show_sma_checkbox 하나로 통제
                    show_rsi_checkbox, rsi_window_slider,
                    show_macd_checkbox, macd_fast_slider, macd_slow_slider, macd_signal_slider
                )

                # 차트 생성
                st.subheader("📈 주가 및 기술적 지표")
                
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2]) # 패널 높이 비율

                # 1. 가격 차트 (캔들스틱) 및 이동평균선
                fig.add_trace(go.Candlestick(x=hist_data_ta.index,
                                            open=hist_data_ta['Open'], high=hist_data_ta['High'],
                                            low=hist_data_ta['Low'], close=hist_data_ta['Close'],
                                            name='캔들스틱'), row=1, col=1)
                if show_sma_checkbox: # UI에서 SMA 표시를 선택했을 때만 그림
                    if f'SMA_{sma_short_window_slider}' in hist_data_ta.columns:
                        fig.add_trace(go.Scatter(x=hist_data_ta.index, y=hist_data_ta[f'SMA_{sma_short_window_slider}'], 
                                                mode='lines', name=f'SMA {sma_short_window_slider}', line=dict(color='orange')), row=1, col=1)
                    if f'SMA_{sma_long_window_slider}' in hist_data_ta.columns:
                        fig.add_trace(go.Scatter(x=hist_data_ta.index, y=hist_data_ta[f'SMA_{sma_long_window_slider}'], 
                                                mode='lines', name=f'SMA {sma_long_window_slider}', line=dict(color='purple')), row=1, col=1)
                
                # 거래량 바 차트
                fig.add_trace(go.Bar(x=hist_data_ta.index, y=hist_data_ta['Volume'], name='거래량', marker_color='rgba(180,180,200,0.5)'), secondary_y=True, row=1, col=1) # secondary_y 사용
                fig.update_layout(yaxis2=dict(title='거래량', overlaying='y', side='right', showgrid=False, range=[0, hist_data_ta['Volume'].max()*3]))


                # 2. RSI 차트
                if show_rsi_checkbox and 'RSI' in hist_data_ta.columns:
                    fig.add_trace(go.Scatter(x=hist_data_ta.index, y=hist_data_ta['RSI'], mode='lines', name='RSI', line=dict(color='green')), row=2, col=1)
                    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="과매수(70)", annotation_position="bottom right", row=2, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="blue", annotation_text="과매도(30)", annotation_position="bottom right", row=2, col=1)
                    fig.update_yaxes(range=[0, 100], row=2, col=1) 

                # 3. MACD 차트
                macd_base_col = f'_{macd_fast_slider}_{macd_slow_slider}_{macd_signal_slider}'
                if show_macd_checkbox and f'MACD{macd_base_col}' in hist_data_ta.columns:
                    fig.add_trace(go.Scatter(x=hist_data_ta.index, y=hist_data_ta[f'MACD{macd_base_col}'], mode='lines', name='MACD', line=dict(color='blue')), row=3, col=1)
                    fig.add_trace(go.Scatter(x=hist_data_ta.index, y=hist_data_ta[f'MACDs{macd_base_col}'], mode='lines', name='Signal', line=dict(color='red')), row=3, col=1)
                    fig.add_trace(go.Bar(x=hist_data_ta.index, y=hist_data_ta[f'MACDh{macd_base_col}'], name='Histogram', marker_color='rgba(100,100,100,0.7)'), row=3, col=1)
                    fig.add_hline(y=0, line_dash="solid", line_color="black", row=3, col=1)

                fig.update_layout(
                    height=750, # 차트 높이 조정
                    xaxis_rangeslider_visible=False, 
                    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
                    margin=dict(l=20, r=20, t=30, b=20) 
                )
                # 각 subplot의 y축 타이틀 설정
                fig.update_yaxes(title_text="가격 (USD)", row=1, col=1, secondary_y=False) # 가격 y축
                if show_rsi_checkbox: fig.update_yaxes(title_text="RSI", row=2, col=1)
                if show_macd_checkbox: fig.update_yaxes(title_text="MACD", row=3, col=1)
                
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("---")

                # 주요 재무 데이터 탭으로 표시
                st.subheader("📑 주요 재무 데이터 (연간)")
                tab1, tab2, tab3 = st.tabs(["손익계산서", "대차대조표", "현금흐름표"])

                with tab1:
                    if financials is not None and not financials.empty:
                        st.dataframe(financials.iloc[:, :4].style.format("{:,.0f}", na_rep="-")) # 최근 4개년도
                    else:
                        st.info(f"{ticker_symbol}의 연간 손익계산서 정보를 가져올 수 없습니다. 일부 종목은 데이터가 제공되지 않을 수 있습니다.")
                with tab2:
                    if balance_sheet is not None and not balance_sheet.empty:
                        st.dataframe(balance_sheet.iloc[:, :4].style.format("{:,.0f}", na_rep="-"))
                    else:
                        st.info(f"{ticker_symbol}의 연간 대차대조표 정보를 가져올 수 없습니다.")
                with tab3:
                    if cashflow is not None and not cashflow.empty:
                        st.dataframe(cashflow.iloc[:, :4].style.format("{:,.0f}", na_rep="-"))
                    else:
                        st.info(f"{ticker_symbol}의 연간 현금흐름표 정보를 가져올 수 없습니다.")
                st.markdown("---")
                
                # 간단 가치 평가
                st.subheader("밸류에이션 참고 (매우 간략화됨)")
                val_col1, val_col2 = st.columns(2)

                with val_col1:
                    st.markdown("##### PER 기반 참고치")
                    current_pe = info.get('trailingPE', None)
                    eps_current = info.get('trailingEps', None)
                    
                    if current_pe and eps_current:
                        st.write(f"현재 PER (TTM): **{current_pe:.2f}**")
                        st.write(f"현재 EPS (TTM): **${eps_current:.2f}**")
                        
                        assumed_pe = st.number_input("적용할 목표 PER:", 
                                                     value=round(float(current_pe),1) if isinstance(current_pe, (int, float)) else 20.0, 
                                                     min_value=1.0, max_value=200.0, step=0.1, key="target_pe_input",
                                                     format="%.1f")
                        estimated_price_pe = eps_current * assumed_pe
                        st.success(f"➡️ 목표 PER 적용 시 참고 주가: **${estimated_price_pe:.2f}**")
                    else:
                        st.warning("PER 또는 EPS 정보가 부족하여 계산할 수 없습니다.")

                with val_col2:
                    st.markdown("##### PBR 기반 참고치")
                    current_pbr = info.get('priceToBook', None)
                    # yfinance info에는 bookValuePerShare가 직접적으로 없을 수 있음.
                    # currentPrice / PBR = Book Value Per Share
                    book_value_per_share_calc = None
                    if current_price and isinstance(current_price, (int,float)) and current_pbr and isinstance(current_pbr, (int,float)) and current_pbr != 0:
                        book_value_per_share_calc = current_price / current_pbr

                    if current_pbr:
                        st.write(f"현재 PBR: **{current_pbr:.2f}**")
                        if book_value_per_share_calc:
                            st.write(f"계산된 BPS (주당순자산): **${book_value_per_share_calc:.2f}**")
                        
                        assumed_pbr = st.number_input("적용할 목표 PBR:",
                                                      value=round(float(current_pbr),1) if isinstance(current_pbr, (int,float)) else 1.0,
                                                      min_value=0.1, max_value=50.0, step=0.1, key="target_pbr_input",
                                                      format="%.1f")
                        if book_value_per_share_calc:
                            estimated_price_pbr = book_value_per_share_calc * assumed_pbr
                            st.success(f"➡️ 목표 PBR 적용 시 참고 주가: **${estimated_price_pbr:.2f}**")
                        else:
                             st.warning("BPS 정보가 부족하여 PBR 기반 추정 주가를 계산할 수 없습니다.")
                    else:
                        st.warning("PBR 정보가 부족합니다.")

                st.info("💡 위 평가는 매우 단순화된 참고용이며, 실제 투자 결정에 사용되어서는 안 됩니다. DCF, RIM 등 더 정교한 모델과 종합적인 분석이 필요합니다. 이 부분은 향후 앱 기능 확장을 통해 개선될 수 있습니다.")

        except Exception as e:
            st.error(f"'{ticker_symbol}' 데이터 처리 중 예상치 못한 오류가 발생했습니다: {str(e)}")
            st.error("인터넷 연결을 확인하거나, 티커 심볼이 정확한지 다시 한번 확인해주세요. (예: 미국 주식 AAPL, MSFT, GOOGL)")
            st.error("문제가 지속되면 잠시 후 다시 시도해주세요. (데이터 제공처의 일시적인 제한일 수 있습니다.)")

    elif analyze_button and not ticker_symbol:
        st.warning("⚠️ 분석할 종목 티커를 사이드바에 입력해주세요.")
    else:
        st.info("👈 사이드바에서 분석할 미국 주식의 티커를 입력하고 '분석 시작!' 버튼을 눌러주세요. 예시 티커: AAPL, MSFT, GOOGL, NVDA, TSLA 등")

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
    ```

이 코드가 우리가 만들고자 하는 웹 애플리케이션의 초기 버전입니다. 주가 정보 조회, 기본적인 기술적 지표와 차트 표시, 주요 재무제표 조회, 그리고 아주 간단한 형태의 가치 평가 참고치를 제공합니다.

이제 이 코드를 GitHub에 올리시고, 다음 단계인 Streamlit Community Cloud 배포를 진행하시면 됩니다! 막히는 부분이 있으면 언제든지 해당 단계 번호와 함께 질문해주세요.