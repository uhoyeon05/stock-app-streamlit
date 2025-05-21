import streamlit as st

st.set_page_config(page_title="테스트 앱", layout="wide")

st.title("👋 안녕하세요! 테스트 앱입니다.")
st.write("이 메시지가 웹 브라우저에 정상적으로 보인다면,")
st.write("Streamlit 앱 배포 자체는 성공적으로 이루어진 것입니다.")
st.success("배포 테스트 성공! 🎉")

if st.button("풍선 효과 보기 🎈"):
    st.balloons()
