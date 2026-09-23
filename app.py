import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Page Configuration (Mobile Responsive)
st.set_page_config(page_title="Biomass ERP & Billing", page_icon="🏭", layout="wide")

# Database Setup
conn = sqlite3.connect("pellet_plant.db", check_same_thread=False)
c = conn.cursor()

# Tables Creation
c.execute('''CREATE TABLE IF NOT EXISTS raw_material_inward (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, gate_pass_no TEXT, supplier TEXT, truck_no TEXT,
                gross_wt REAL, tare_wt REAL, net_wt REAL, rate_per_ton REAL,
                moisture REAL, ash REAL, foreign_matter TEXT, qc_status TEXT,
                deduction REAL, total_payable REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS production_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, shift TEXT, start_time TEXT, stop_time TEXT,
                run_hours REAL, stop_reason TEXT, input_tons REAL,
                output_tons REAL, screening_loss REAL, moisture_loss REAL,
                yield_efficiency REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS outward_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, invoice_no TEXT, buyer TEXT, truck_no TEXT,
                tare_wt REAL, gross_wt REAL, net_wt REAL, rate_per_ton REAL,
                tax_type TEXT, taxable_amt REAL, gst_amt REAL, total_invoice REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS plant_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, category TEXT, amount REAL, payment_mode TEXT,
                vendor TEXT, remarks TEXT)''')
conn.commit()

# Sidebar Navigation
st.sidebar.title("🏭 Biomass Plant ERP")
menu = st.sidebar.radio("Go to Module:", [
    "1. Inward Husk (Gate Pass & QC)",
    "2. Machine Production & Loss Log",
    "3. Outward Sales & Tax Invoice",
    "4. Daily Plant Expenses",
    "5. 📄 Gate Pass & Invoice Printing",
    "6. 📊 Reports & Excel Export"
])

# -------------------------------------------------------------
# MODULE 1: INWARD & QC
# -------------------------------------------------------------
if menu == "1. Inward Husk (Gate Pass & QC)":
    st.title("🌾 Inward Raw Material Entry")
    with st.form("inward_form"):
        col1, col2 = st.columns(2)
        with col1:
            supplier = st.text_input("Supplier / Mill Name")
            truck_no = st.text_input("Truck Number").upper()
            gross_wt = st.number_input("Gross Weight (Loaded Tons)", min_value=0.0, step=0.01)
            tare_wt = st.number_input("Tare Weight (Empty Tons)", min_value=0.0, step=0.01)
            rate = st.number_input("Purchase Rate / Ton (₹)", min_value=0.0, step=50.0)
        with col2:
            moisture = st.number_input("Moisture %", min_value=0.0, max_value=100.0, value=10.0)
            ash = st.number_input("Ash Content %", min_value=0.0, max_value=100.0, value=16.0)
            foreign = st.selectbox("Stone/Soil Impurities", ["None", "Minor", "High"])
            qc_status = st.selectbox("QC Decision", ["Accepted", "Accepted with Deduction", "Rejected"])
            deduction = st.number_input("Deduction (₹)", min_value=0.0, step=100.0)

        submitted = st.form_submit_button("💾 Save & Create Gate Pass")
        if submitted:
            if gross_wt > tare_wt and supplier and truck_no:
                net_wt = gross_wt - tare_wt
                total_payable = (net_wt * rate) - deduction
                gp_no = f"GP-IN-{datetime.now().strftime('%d%H%M%S')}"
                today = datetime.now().strftime("%Y-%m-%d")
                c.execute('''INSERT INTO raw_material_inward (date, gate_pass_no, supplier, truck_no, gross_wt, tare_wt, net_wt, rate_per_ton, moisture, ash, foreign_matter, qc_status, deduction, total_payable)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                          (today, gp_no, supplier, truck_no, gross_wt, tare_wt, net_wt, rate, moisture, ash, foreign, qc_status, deduction, total_payable))
                conn.commit()
                st.success(f"Inward Gate Pass Generated: {gp_no}")
            else:
                st.error("Kripya valid weights aur supplier details bharein!")

# -------------------------------------------------------------
# MODULE 2: PRODUCTION
# -------------------------------------------------------------
elif menu == "2. Machine Production & Loss Log":
    st.title("⚙️ Machine Production & Loss Log")
    st.caption("2 TPH Capacity Tracker")
    shift = st.selectbox("Shift", ["Shift 1", "Shift 2"])
    with st.form("prod_form"):
        col1, col2 = st.columns(2)
        with col1:
            input_tons = st.number_input("Raw Husk Consumed (Tons)", min_value=0.0, step=0.1)
            output_tons = st.number_input("Finished Pellets (Tons)", min_value=0.0, step=0.1)
        with col2:
            screen_loss = st.number_input("Screening Waste (Tons)", min_value=0.0, step=0.1)
            moist_loss = st.number_input("Moisture/Dust Loss (Tons)", min_value=0.0, step=0.1)
        reason = st.text_input("Operational / Maintenance Note", "Smooth Run")
        if st.form_submit_button("Submit Production Record"):
            if input_tons > 0:
                eff = round((output_tons / input_tons) * 100, 2)
                today = datetime.now().strftime("%Y-%m-%d")
                c.execute('''INSERT INTO production_logs (date, shift, start_time, stop_time, run_hours, stop_reason, input_tons, output_tons, screening_loss, moisture_loss, yield_efficiency)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                          (today, shift, "Auto", "Auto", 8.0, reason, input_tons, output_tons, screen_loss, moist_loss, eff))
                conn.commit()
                st.success(f"Saved! Yield Efficiency: {eff}%")

# -------------------------------------------------------------
# MODULE 3: SALES & OUTWARD
# -------------------------------------------------------------
elif menu == "3. Outward Sales & Tax Invoice":
    st.title("🚚 Outward Sales & Tax Invoice")
    with st.form("sales_form"):
        c1, c2 = st.columns(2)
        with c1:
            buyer = st.text_input("Buyer / Company Name")
            truck_no = st.text_input("Truck Number").upper()
            tare = st.number_input("Tare Weight (Empty Tons)", min_value=0.0, step=0.01)
            gross = st.number_input("Gross Weight (Loaded Tons)", min_value=0.0, step=0.01)
        with c2:
            rate = st.number_input("Selling Rate / Ton (₹)", min_value=0.0, value=6500.0)
            tax_type = st.selectbox("GST Type", ["IntraState (CGST 2.5% + SGST 2.5%)", "InterState (IGST 5%)"])
        if st.form_submit_button("Generate Outward Invoice"):
            if gross > tare and buyer:
                net = gross - tare
                taxable = net * rate
                gst = taxable * 0.05
                total = taxable + gst
                inv_no = f"INV-{datetime.now().strftime('%d%H%M%S')}"
                today = datetime.now().strftime("%Y-%m-%d")
                c.execute('''INSERT INTO outward_sales (date, invoice_no, buyer, truck_no, tare_wt, gross_wt, net_wt, rate_per_ton, tax_type, taxable_amt, gst_amt, total_invoice)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                          (today, inv_no, buyer, truck_no, tare, gross, net, rate, tax_type, taxable, gst, total))
                conn.commit()
                st.success(f"Invoice {inv_no} Created!")

# -------------------------------------------------------------
# MODULE 4: EXPENSES
# -------------------------------------------------------------
elif menu == "4. Daily Plant Expenses":
    st.title("💸 Daily Plant Expenses")
    with st.form("exp_form"):
        cat = st.selectbox("Category", ["Hospitality (Tea & Snacks)", "Wear & Tear Spares", "Fuel (Diesel)", "Maintenance", "Misc"])
        amt = st.number_input("Amount (₹)", min_value=0.0)
        mode = st.selectbox("Mode", ["Cash", "UPI", "Bank"])
        rem = st.text_input("Remarks / Item Description")
        if st.form_submit_button("Save Expense"):
            if amt > 0:
                c.execute("INSERT INTO plant_expenses (date, category, amount, payment_mode, vendor, remarks) VALUES (?,?,?,?,?,?)",
                          (datetime.now().strftime("%Y-%m-%d"), cat, amt, mode, "-", rem))
                conn.commit()
                st.success("Expense Logged!")

# -------------------------------------------------------------
# MODULE 5: GATE PASS & INVOICE PRINTING / VIEW
# -------------------------------------------------------------
elif menu == "5. 📄 Gate Pass & Invoice Printing":
    st.title("📄 Gate Pass & Invoice Print Center")
    doc_type = st.radio("Choose Document to Print:", ["Inward Gate Pass (Husk)", "Sales Tax Invoice (Pellets)"], horizontal=True)

    if doc_type == "Inward Gate Pass (Husk)":
        df = pd.read_sql("SELECT id, gate_pass_no, supplier, truck_no, net_wt, total_payable FROM raw_material_inward ORDER BY id DESC", conn)
        if not df.empty:
            selected_id = st.selectbox("Select Gate Pass to View & Print:", df['gate_pass_no'].tolist())
            record = pd.read_sql(f"SELECT * FROM raw_material_inward WHERE gate_pass_no = '{selected_id}'", conn).iloc[0]

            st.markdown(f"""
            <div style="border: 2px solid #333; padding: 20px; border-radius: 8px; background-color: #fff; color: #000; font-family: monospace;">
                <h2 style="text-align: center; margin: 0;">BIOMASS MANUFACTURING PLANT</h2>
                <h4 style="text-align: center; margin: 5px 0 15px 0; border-bottom: 1px solid #ccc;">INWARD GOODS RECEIPT & GATE PASS</h4>
                <table style="width: 100%; font-size: 14px; line-height: 1.8;">
                    <tr><td><b>Gate Pass No:</b> {record['gate_pass_no']}</td><td><b>Date:</b> {record['date']}</td></tr>
                    <tr><td><b>Supplier:</b> {record['supplier']}</td><td><b>Truck No:</b> {record['truck_no']}</td></tr>
                    <tr><td><b>Gross Weight:</b> {record['gross_wt']} Tons</td><td><b>Tare Weight:</b> {record['tare_wt']} Tons</td></tr>
                    <tr><td><b>Net Husk Weight:</b> <span style="font-size: 16px; color: green;"><b>{record['net_wt']} Tons</b></span></td><td><b>Rate / Ton:</b> ₹{record['rate_per_ton']}</td></tr>
                    <tr><td><b>Moisture Level:</b> {record['moisture']}%</td><td><b>Foreign Matter:</b> {record['foreign_matter']}</td></tr>
                    <tr><td><b>QC Status:</b> {record['qc_status']}</td><td><b>Deductions:</b> ₹{record['deduction']}</td></tr>
                    <tr><td colspan="2" style="border-top: 1px solid #ccc; padding-top: 10px; font-size: 16px;"><b>Net Payable Amount:</b> ₹{record['total_payable']}</td></tr>
                </table>
                <br><br>
                <div style="display: flex; justify-content: space-between; font-size: 12px;">
                    <span>____________________<br>Weighbridge Clerk</span>
                    <span>____________________<br>Driver Signature</span>
                    <span>____________________<br>Authorised Signatory</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Abhi koi Inward Gate Pass available nahi hai.")

    elif doc_type == "Sales Tax Invoice (Pellets)":
        df = pd.read_sql("SELECT id, invoice_no, buyer, truck_no, net_wt, total_invoice FROM outward_sales ORDER BY id DESC", conn)
        if not df.empty:
            selected_inv = st.selectbox("Select Invoice to View & Print:", df['invoice_no'].tolist())
            rec = pd.read_sql(f"SELECT * FROM outward_sales WHERE invoice_no = '{selected_inv}'", conn).iloc[0]

            st.markdown(f"""
            <div style="border: 2px solid #1e3a8a; padding: 20px; border-radius: 8px; background-color: #fff; color: #000; font-family: sans-serif;">
                <h2 style="text-align: center; color: #1e3a8a; margin: 0;">TAX INVOICE / DISPATCH CHALLAN</h2>
                <p style="text-align: center; font-size: 12px; margin: 0 0 10px 0;">Manufacturer of High Density Rice Husk Biomass Pellets</p>
                <hr>
                <table style="width: 100%; font-size: 14px; line-height: 1.8;">
                    <tr><td><b>Invoice No:</b> {rec['invoice_no']}</td><td><b>Date:</b> {rec['date']}</td></tr>
                    <tr><td><b>Billed To (Buyer):</b> {rec['buyer']}</td><td><b>Vehicle No:</b> {rec['truck_no']}</td></tr>
                    <tr><td><b>Net Pellets Weight:</b> <b>{rec['net_wt']} Tons</b></td><td><b>Rate per Ton:</b> ₹{rec['rate_per_ton']}</td></tr>
                    <tr><td><b>Taxable Amount:</b> ₹{rec['taxable_amt']}</td><td><b>GST (5%):</b> ₹{rec['gst_amt']}</td></tr>
                    <tr style="background: #f0fdf4; font-size: 18px;"><td colspan="2" style="padding: 10px;"><b>Total Invoice Value:</b> ₹{rec['total_invoice']}</td></tr>
                </table>
                <br><br>
                <div style="display: flex; justify-content: space-between; font-size: 12px;">
                    <span>Receiver's Stamp & Sign</span>
                    <span>For Biomass Pellets Plant (Authorized Signatory)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Abhi koi Sales Invoice available nahi hai.")

# -------------------------------------------------------------
# MODULE 6: MASTER REPORTS & EXCEL DOWNLOAD
# -------------------------------------------------------------
elif menu == "6. 📊 Reports & Excel Export":
    st.title("📊 Plant Reports & Data Export")

    rep_type = st.selectbox("Select Report Category:", [
        "Daily Production & Loss Report",
        "Raw Material Inward Stock Report",
        "Outward Sales & Revenue Register",
        "Plant Expense Summary"
    ])

    if rep_type == "Daily Production & Loss Report":
        df = pd.read_sql("SELECT date, shift, run_hours, input_tons, output_tons, screening_loss, moisture_loss, yield_efficiency, stop_reason FROM production_logs ORDER BY id DESC", conn)
    elif rep_type == "Raw Material Inward Stock Report":
        df = pd.read_sql("SELECT date, gate_pass_no, supplier, truck_no, net_wt, rate_per_ton, total_payable, qc_status FROM raw_material_inward ORDER BY id DESC", conn)
    elif rep_type == "Outward Sales & Revenue Register":
        df = pd.read_sql("SELECT date, invoice_no, buyer, truck_no, net_wt, rate_per_ton, taxable_amt, gst_amt, total_invoice FROM outward_sales ORDER BY id DESC", conn)
    elif rep_type == "Plant Expense Summary":
        df = pd.read_sql("SELECT date, category, amount, payment_mode, remarks FROM plant_expenses ORDER BY id DESC", conn)

    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Download {rep_type} (Excel/CSV File)",
            data=csv,
            file_name=f"{rep_type.replace(' ', '_')}_{datetime.now().strftime('%d_%b')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.warning("Is category me abhi koi data record nahi hua hai.")
