import streamlit as st
import pandas as pd
import sqlite3
import re
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="HealthPrediction AI", page_icon="🏥", layout="wide")

# Modern Healthcare CSS
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Custom button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 28px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Header styling */
    .health-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    .health-header h1 {
        color: white;
        margin: 0;
        font-size: 32px;
        font-weight: 700;
    }
    .health-header p {
        color: rgba(255,255,255,0.9);
        margin-top: 10px;
        font-size: 16px;
    }
    
    /* Card styling */
    .health-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    .health-card:hover {
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    /* Info box */
    .prediction-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        border-left: 5px solid #667eea;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
        margin-top: 8px;
    }
    
    /* Warning box */
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    /* Success box */
    .success-box {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        border-top: 1px solid #e0e0e0;
        margin-top: 40px;
    }
    
    /* Input fields */
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #ddd;
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Database setup
conn = sqlite3.connect('healthcare.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS patients
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              full_name TEXT NOT NULL,
              dob TEXT NOT NULL,
              email TEXT UNIQUE NOT NULL,
              glucose REAL NOT NULL,
              haemoglobin REAL NOT NULL,
              cholesterol REAL NOT NULL,
              remarks TEXT,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()
conn.close()

def get_ai_prediction(glucose, haemoglobin, cholesterol):
    conditions = []
    risk_score = 0
    
    if glucose > 140:
        conditions.append(f"⚠️ Elevated Glucose: {glucose} mg/dL - Diabetes Screening Recommended")
        risk_score += 40
    elif glucose < 70:
        conditions.append(f"⚠️ Low Glucose: {glucose} mg/dL - Monitor for Hypoglycemia")
        risk_score += 20
    else:
        conditions.append(f"✅ Optimal Glucose: {glucose} mg/dL")
    
    if haemoglobin < 12:
        conditions.append(f"⚠️ Low Hemoglobin: {haemoglobin} g/dL - Anemia Evaluation Needed")
        risk_score += 30
    elif haemoglobin > 17:
        conditions.append(f"⚠️ Elevated Hemoglobin: {haemoglobin} g/dL")
    else:
        conditions.append(f"✅ Normal Hemoglobin: {haemoglobin} g/dL")
    
    if cholesterol > 240:
        conditions.append(f"⚠️ High Cholesterol: {cholesterol} mg/dL - Cardiovascular Assessment Required")
        risk_score += 30
    elif cholesterol > 200:
        conditions.append(f"⚠️ Borderline Cholesterol: {cholesterol} mg/dL - Lifestyle Modifications Advised")
        risk_score += 15
    else:
        conditions.append(f"✅ Healthy Cholesterol: {cholesterol} mg/dL")
    
    # Overall assessment
    if risk_score >= 60:
        assessment = "🔴 HIGH RISK - Immediate medical consultation strongly recommended"
    elif risk_score >= 30:
        assessment = "🟡 MODERATE RISK - Schedule follow-up within 3 months"
    else:
        assessment = "🟢 LOW RISK - Continue current health practices"
    
    return {
        "conditions": " | ".join(conditions),
        "risk_score": risk_score,
        "assessment": assessment
    }

def validate_email(email):
    return email.lower().endswith('@gmail.com')

def create_patient(name, dob, email, glucose, hb, cholesterol, remark):
    try:
        conn = sqlite3.connect('healthcare.db')
        c = conn.cursor()
        c.execute("INSERT INTO patients (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks) VALUES (?,?,?,?,?,?,?)",
                  (name, dob, email, glucose, hb, cholesterol, remark))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_all_patients():
    conn = sqlite3.connect('healthcare.db')
    c = conn.cursor()
    c.execute("SELECT * FROM patients ORDER BY created_at DESC")
    data = c.fetchall()
    conn.close()
    return data

def get_patient_by_id(pid):
    conn = sqlite3.connect('healthcare.db')
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE id = ?", (pid,))
    data = c.fetchone()
    conn.close()
    return data

def update_patient(pid, name, dob, email, glucose, hb, cholesterol, remark):
    try:
        conn = sqlite3.connect('healthcare.db')
        c = conn.cursor()
        c.execute("UPDATE patients SET full_name=?, dob=?, email=?, glucose=?, haemoglobin=?, cholesterol=?, remarks=? WHERE id=?",
                  (name, dob, email, glucose, hb, cholesterol, remark, pid))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def delete_patient(pid):
    conn = sqlite3.connect('healthcare.db')
    c = conn.cursor()
    c.execute("DELETE FROM patients WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    return True

# Header
st.markdown("""
<div class="health-header">
    <h1>🏥 AI-Powered Health Prediction System</h1>
    <p>Intelligent Patient Management with Clinical Decision Support</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📋 Navigation")
    menu = st.selectbox(
        "",
        ["➕ Register Patient", "📊 Patient Database", "✏️ Update Records", "🗑️ Delete Records", "📈 Analytics"]
    )
    st.markdown("---")
    st.markdown("### 💡 About")
    st.info("This system uses AI to analyze patient health data and provide clinical predictions based on blood test results.")

# REGISTER PATIENT
if menu == "➕ Register Patient":
    st.markdown("### 📝 New Patient Registration")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("👤 Full Name", placeholder="Enter patient's full name")
        dob = st.date_input("📅 Date of Birth", min_value=datetime(1900, 1, 1),
                           max_value=datetime.now().date(), value=datetime(2000, 1, 1))
        email = st.text_input("📧 Email Address", placeholder="patient@gmail.com", 
                             help="Only Gmail addresses are accepted")
        
    with col2:
        glucose = st.number_input("🩸 Glucose Level (mg/dL)", min_value=0.0, max_value=500.0, value=100.0, step=1.0,
                                 help="Normal range: 70-140 mg/dL")
        haemoglobin = st.number_input("💉 Hemoglobin (g/dL)", min_value=0.0, max_value=20.0, value=13.5, step=0.1,
                                     help="Normal: Male 13.5-17.5, Female 12.0-15.5")
        cholesterol = st.number_input("❤️ Cholesterol (mg/dL)", min_value=0.0, max_value=500.0, value=180.0, step=1.0,
                                     help="Optimal: Below 200 mg/dL")
    
    if st.button("🚀 Generate Health Prediction", type="primary"):
        # Validation
        errors = []
        if not name:
            errors.append("Patient name is required")
        if dob > datetime.now().date():
            errors.append("Date of birth cannot be in the future")
        if not email:
            errors.append("Email address is required")
        elif not validate_email(email):
            errors.append("Only Gmail addresses (@gmail.com) are accepted")
        if glucose <= 0:
            errors.append("Valid glucose level is required")
        if haemoglobin <= 0:
            errors.append("Valid hemoglobin level is required")
        if cholesterol <= 0:
            errors.append("Valid cholesterol level is required")
        
        if errors:
            for error in errors:
                st.error(f"• {error}")
        else:
            with st.spinner("🤖 AI analyzing clinical data..."):
                prediction = get_ai_prediction(glucose, haemoglobin, cholesterol)
                remark = f"{prediction['conditions']}\n\nRisk Score: {prediction['risk_score']}/100\n\nAssessment: {prediction['assessment']}"
            
            if create_patient(name, dob, email, glucose, haemoglobin, cholesterol, remark):
                st.success(f"✅ {name} has been successfully registered!")
                
                st.markdown(f"""
                <div class="prediction-box">
                    <strong>🤖 AI Clinical Prediction:</strong><br><br>
                    {prediction['conditions']}<br><br>
                    <strong>Risk Score:</strong> {prediction['risk_score']}/100<br>
                    <strong>Assessment:</strong> {prediction['assessment']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("❌ Registration failed - Email address already exists in database")

# VIEW RECORDS
elif menu == "📊 Patient Database":
    st.markdown("### 📊 Patient Health Records")
    st.markdown("---")
    
    records = get_all_patients()
    
    if records:
        df = pd.DataFrame(records, columns=["ID", "Name", "DOB", "Email", "Glucose", "Hb", "Cholesterol", "Remarks", "Created"])
        
        # Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(df)}</div>
                <div class="metric-label">Total Patients</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            high_glucose = len(df[df['Glucose'] > 140])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #dc2626;">{high_glucose}</div>
                <div class="metric-label">Diabetes Risk</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            high_chol = len(df[df['Cholesterol'] > 200])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #f59e0b;">{high_chol}</div>
                <div class="metric-label">Cardiovascular Risk</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            low_hb = len(df[df['Hb'] < 12])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #8b5cf6;">{low_hb}</div>
                <div class="metric-label">Anemia Risk</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Display table
        st.dataframe(df[["ID", "Name", "Email", "Glucose", "Hb", "Cholesterol"]], use_container_width=True)
        
        # Detailed view
        st.markdown("### 🔍 Patient Health Summary")
        selected_id = st.selectbox("Select Patient", df['ID'].tolist())
        if selected_id:
            patient = [p for p in records if p[0] == selected_id][0]
            dob_date = datetime.strptime(patient[2], '%Y-%m-%d')
            age = datetime.now().year - dob_date.year
            
            st.markdown(f"""
            <div class="health-card">
                <h3 style="color: #667eea;">{patient[1]}</h3>
                <table style="width: 100%;">
                    <tr>
                        <td><strong>📧 Email:</strong></td>
                        <td>{patient[3]}</td>
                        <td><strong>🎂 Age:</strong></td>
                        <td>{age} years</td>
                    </tr>
                    <tr>
                        <td><strong>🩸 Glucose:</strong></td>
                        <td>{patient[4]} mg/dL</td>
                        <td><strong>💉 Hemoglobin:</strong></td>
                        <td>{patient[5]} g/dL</td>
                    </tr>
                    <tr>
                        <td><strong>❤️ Cholesterol:</strong></td>
                        <td>{patient[6]} mg/dL</td>
                        <td><strong>📅 Record ID:</strong></td>
                        <td>#{patient[0]}</td>
                    </tr>
                </table>
                <div class="prediction-box" style="margin-top: 15px;">
                    <strong>🤖 AI Health Analysis:</strong><br>
                    {patient[7]}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📭 No patient records found. Use the registration form to add patients.")

# UPDATE RECORD
elif menu == "✏️ Update Records":
    st.markdown("### ✏️ Update Patient Information")
    st.markdown("---")
    
    records = get_all_patients()
    if records:
        selected = st.selectbox("Select Patient", [f"{p[1]} (ID: {p[0]})" for p in records])
        pid = int(selected.split("ID: ")[1].rstrip(")"))
        patient = [p for p in records if p[0] == pid][0]
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", patient[1])
            dob = st.date_input("Date of Birth", datetime.strptime(patient[2], '%Y-%m-%d').date())
            email = st.text_input("Email", patient[3])
        with col2:
            glucose = st.number_input("Glucose (mg/dL)", value=float(patient[4]))
            haemoglobin = st.number_input("Hemoglobin (g/dL)", value=float(patient[5]))
            cholesterol = st.number_input("Cholesterol (mg/dL)", value=float(patient[6]))
        
        if st.button("Update Health Record", type="primary"):
            if not validate_email(email):
                st.error("Only Gmail addresses are accepted")
            else:
                with st.spinner("Updating AI prediction..."):
                    prediction = get_ai_prediction(glucose, haemoglobin, cholesterol)
                    remark = f"{prediction['conditions']}\n\nRisk Score: {prediction['risk_score']}/100\n\nAssessment: {prediction['assessment']}"
                
                if update_patient(pid, name, dob, email, glucose, haemoglobin, cholesterol, remark):
                    st.success("✅ Patient record updated successfully!")
                    st.info("New AI prediction has been generated based on updated values.")
                else:
                    st.error("Update failed")
    else:
        st.info("No records available for update")

# DELETE RECORD
elif menu == "🗑️ Delete Records":
    st.markdown("### 🗑️ Remove Patient Record")
    st.markdown("---")
    
    records = get_all_patients()
    if records:
        selected = st.selectbox("Select Patient", [f"{p[1]} (ID: {p[0]})" for p in records])
        pid = int(selected.split("ID: ")[1].rstrip(")"))
        patient = get_patient_by_id(pid)
        
        if patient:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="health-card">
                    <strong>📋 Patient Information</strong><br><br>
                    <strong>Name:</strong> {patient[1]}<br>
                    <strong>Email:</strong> {patient[3]}<br>
                    <strong>Record ID:</strong> #{patient[0]}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="health-card">
                    <strong>🏥 Latest Values</strong><br><br>
                    <strong>Glucose:</strong> {patient[4]} mg/dL<br>
                    <strong>Hemoglobin:</strong> {patient[5]} g/dL<br>
                    <strong>Cholesterol:</strong> {patient[6]} mg/dL
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="warning-box">
                <strong>⚠️ Confirmation Required</strong><br>
                This action is permanent and cannot be reversed. All patient data will be removed.
            </div>
            """, unsafe_allow_html=True)
            
            confirm = st.checkbox("I understand that this action is permanent")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Delete Permanently", disabled=not confirm):
                    if delete_patient(pid):
                        st.success(f"✅ {patient[1]} has been removed from the database")
                        st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.info("Deletion cancelled")
    else:
        st.info("No records available for deletion")

# ANALYTICS
elif menu == "📈 Analytics":
    st.markdown("### 📊 Healthcare Analytics Dashboard")
    st.markdown("---")
    
    records = get_all_patients()
    if records:
        df = pd.DataFrame(records, columns=["ID", "Name", "DOB", "Email", "Glucose", "Hb", "Cholesterol", "Remarks", "Created"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Glucose Distribution")
            fig = px.histogram(df, x='Glucose', title='Patient Glucose Levels',
                              color_discrete_sequence=['#667eea'], nbins=20)
            fig.update_layout(plot_bgcolor='white', height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Health Parameters Correlation")
            fig = px.scatter(df, x='Glucose', y='Cholesterol', size='Hb', 
                           hover_data=['Name'], title='Glucose vs Cholesterol Analysis',
                           color_discrete_sequence=['#764ba2'])
            fig.update_layout(plot_bgcolor='white', height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### Risk Distribution")
            risk_data = pd.DataFrame({
                'Risk Category': ['High Glucose', 'High Cholesterol', 'Low Hemoglobin'],
                'Count': [len(df[df['Glucose'] > 140]), 
                         len(df[df['Cholesterol'] > 200]),
                         len(df[df['Hb'] < 12])]
            })
            fig = px.bar(risk_data, x='Risk Category', y='Count', title='Population Health Risks',
                        color='Count', color_continuous_scale='Viridis')
            fig.update_layout(plot_bgcolor='white', height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            st.markdown("#### Key Metrics")
            st.markdown(f"""
            <div class="health-card">
                <strong>📊 Clinical Summary</strong><br><br>
                <strong>Total Enrolled:</strong> {len(df)} patients<br>
                <strong>Average Glucose:</strong> {df['Glucose'].mean():.1f} mg/dL<br>
                <strong>Average Cholesterol:</strong> {df['Cholesterol'].mean():.1f} mg/dL<br>
                <strong>Average Hemoglobin:</strong> {df['Hb'].mean():.1f} g/dL<br>
                <strong>High Risk Patients:</strong> {len(df[(df['Glucose']>140) | (df['Cholesterol']>200) | (df['Hb']<12)])}<br>
                <strong>Data Updated:</strong> {datetime.now().strftime('%Y-%m-%d')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📭 No data available for analytics. Please add patient records first.")

# Footer
st.markdown("""
<div class="footer">
    <p>🏥 AI-Powered Health Prediction System | Intelligent Clinical Decision Support</p>
    <p style="font-size: 12px;">© 2024 | Secure Healthcare Data Management</p>
</div>
""", unsafe_allow_html=True)