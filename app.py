import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import re
import io
from openpyxl import Workbook

FinalData = []
SECRET_PASSWORD = "Manoj9637"

def extract_funnel_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    funnel_cards = soup.find_all('div', {'class': 'card-inner-container'})
    all_funnels = {}

    for card in funnel_cards:
        ScrappedData = {}
        title_elem = card.find('div', {'class': 't-16'})
        if not title_elem:
            continue
        title = title_elem.text.strip()
        ScrappedData["title"] = title

        data_labels = card.find_all(['text', 'tspan'])
        step_labels = card.find_all('span', style=lambda v: v and 'position: absolute' in v)
        steps = [label.text.strip() for label in step_labels]

        conversion_data = []
        seen = set()
        step_index = 0
        for label in data_labels:
            text = label.text.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            ScrappedData[str(step_index)] = text
            step_index += 1

            if '%' in text:
                match = re.search(r'([\d.]+)%\s*\((\d+(?:,\d+)?)\)', text)
                if match:
                    conversion_data.append({
                        'conversion_rate': float(match.group(1)),
                        'users': int(match.group(2).replace(',', ''))
                    })

        if conversion_data:
            if len(steps) < len(conversion_data):
                steps += [f"Step {i+1}" for i in range(len(steps), len(conversion_data))]
            steps = steps[:len(conversion_data)]
            df = pd.DataFrame({
                'step': steps,
                'users': [d['users'] for d in conversion_data],
                'conversion_rate': [d['conversion_rate'] for d in conversion_data]
            })
            all_funnels[title] = df

        FinalData.append(ScrappedData)
    return all_funnels

def generate_excel_in_memory(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "Funnel Data"

    headers = ["Title"]
    for i in range(4):
        headers += [f"Value {i}", f"Percentage {i}"]
    ws.append(headers)

    for item in data:
        row = [item.get("title", "Unknown")]
        for i in range(4):
            val = item.get(str(i), "")
            match = re.search(r'([\d.]+)%\s*\((\d+(?:,\d+)?)\)', val)
            if match:
                users = match.group(2)
                pct = f"{match.group(1)}%"
                row.extend([users, pct])
            else:
                row.extend(["-", "-"])
        ws.append(row)

    excel_io = io.BytesIO()
    wb.save(excel_io)
    excel_io.seek(0)

    df = pd.read_excel(excel_io)
    return df

# ---------------------
# Fake error screen
# ---------------------
st.markdown("<h1 style='color:red;'>🚫 Error 404: Page Not Found</h1>", unsafe_allow_html=True)
st.caption("Please Call ModiJI 😂😂😂😂😂😂😂😂.")  # Suspicious but subtle

if "show_password" not in st.session_state:
    st.session_state["show_password"] = False

if st.button(" "):  # Invisible button under the caption
    st.session_state["show_password"] = True

if st.session_state["show_password"]:
    password = st.text_input("", type="password", label_visibility="collapsed")
    if password == SECRET_PASSWORD:
        st.success("Access Granted!")

        st.title("📄 HTML to Excel Viewer")

        html_input = st.text_area("Paste HTML content", height=300)

        if st.button("Extract & Show Excel"):
            if not html_input.strip():
                st.warning("Paste some HTML first.")
            else:
                FinalData.clear()
                extract_funnel_data(html_input)
                excel_df = generate_excel_in_memory(FinalData)
                st.success("✅ Excel generated and shown below:")
                st.dataframe(excel_df)
    elif password:
        st.error("❌ Incorrect password.")
