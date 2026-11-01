import os
import requests
import streamlit as st
API_URL = os.getenv(
    "BACKEND_URL",
    os.getenv("API_URL", "http://127.0.0.1:8001")
)


st.set_page_config(page_title="Product Review Insights", page_icon="🛍️", layout="centered")
st.title("🛍️ Product Review Insights")
st.caption("AI-powered aspect sentiment analysis and product-team summaries")
review = st.text_area("Paste a customer review", height=160, placeholder="The quality is excellent but delivery was slow...")
technique = st.selectbox("Prompt technique", ["few_shot", "zero_shot", "role_based"], format_func=lambda x:x.replace('_',' ').title())
if st.button("Analyse review", type="primary"):
    if len(review.strip()) < 10:
        st.warning("Please enter at least 10 characters.")
    else:
        try:
            with st.spinner("Analysing..."):
                response = requests.post(f"{API_URL}/analyze", json={"review":review,"technique":technique}, timeout=100)
            if not response.ok:
                st.error(f"Backend error ({response.status_code}): {response.text}")
            else:
                result = response.json()
                insights = result["insights"]
                c1,c2,c3 = st.columns(3)
                c1.metric("Rating guess", f"{insights['rating_guess']}/5")
                c2.metric("Recommend", "Yes" if insights["would_recommend"] else "No")
                c3.metric("Judge score", f"{result['judge']['score']}/5")
                st.subheader("Aspect sentiments")
                if insights["aspects"]:
                    st.dataframe(insights["aspects"], use_container_width=True, hide_index=True)
                else:
                    st.info("No listed aspects mentioned explicitly.")
                st.subheader("Summary for product team")
                st.write(insights["summary"])
                st.subheader("Judge reasoning")
                st.write(result["judge"]["reason"])
                with st.expander("Structured JSON"):
                    st.json(result)
        except requests.RequestException as exc:
            st.error(f"Cannot reach FastAPI: {exc}")
