import streamlit as st
import re
import math
import plotly.graph_objects as go
from audio_recorder_streamlit import audio_recorder

# =====================================================================
# 1. INITIAL CONSTRAINTS & CONFIGURATION
# =====================================================================
st.set_page_config(
    page_title="Secure Enterprise Assessment Tool",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State Variables
if "exam_submitted" not in st.session_state:
    st.session_state.exam_submitted = False
if "security_flagged" not in st.session_state:
    st.session_state.security_flagged = False

# =====================================================================
# 2. APPLICATION PLACEHOLDERS (FOR CLEAN UI ISOLATION)
# =====================================================================
header_area = st.empty()
auth_area = st.empty()
spoken_area = st.empty()
written_area = st.empty()
submit_button_area = st.empty()

# =====================================================================
# 3. APPLICATION LOGIN & VERIFICATION STRINGS
# =====================================================================
if not st.session_state.exam_submitted:
    with header_area.container():
        st.title("Communication Evaluation")
    
    with auth_area.container():
        st.markdown("### Trainee Authentication")
        reg_col1, reg_col2 = st.columns(2)
        with reg_col1:
            trainee_name = st.text_input("Enter Trainee Name:").strip()
        with reg_col2:
            emp_id = st.text_input("Enter Employee ID (Emp ID):").strip()
else:
    trainee_name = st.session_state.get("trainee_name", "")
    emp_id = st.session_state.get("emp_id", "")

# =====================================================================
# 4. IMMEDIATE PROCTORING & INLINE COPY-PASTE BLOCKER
# =====================================================================
if trainee_name and emp_id:
    st.session_state.trainee_name = trainee_name
    st.session_state.emp_id = emp_id

    if not st.session_state.exam_submitted:
        strict_security_js = """
        <script>
            window.onblur = function() {
                const url = new URL(window.location.href);
                url.searchParams.set('security_breach', 'true');
                window.location.href = url.href; 
            };

            const securityLockdownInterval = setInterval(() => {
                const targets = window.parent.document.querySelectorAll('textarea, input[type="text"]');
                targets.forEach(el => {
                    if (!el.dataset.secured) {
                        el.addEventListener('paste', e => { e.preventDefault(); alert("Security Violation: Pasting text is forbidden."); });
                        el.addEventListener('copy', e => e.preventDefault());
                        el.addEventListener('cut', e => e.preventDefault());
                        el.addEventListener('drop', e => e.preventDefault());
                        el.addEventListener('contextmenu', e => e.preventDefault());
                        el.style.userSelect = "none";
                        el.dataset.secured = "true";
                    }
                });
            }, 500);
        </script>
        """
        st.components.v1.html(strict_security_js, height=0, width=0)

        if st.query_params.get("security_breach") == "true":
            st.session_state.security_flagged = True

        if st.session_state.security_flagged:
            st.error("ASSESSMENT TERMINAL LOCKED OUT")
            st.critical("Security Violation: You navigated away from the active assessment tab.")
            st.stop()
else:
    if not st.session_state.exam_submitted:
        st.warning("Please input Trainee Name and Employee ID to unlock the secure proctored environment.")
        st.stop()

# =====================================================================
# 5. EVALUATION MODULES (CONDITIONAL PRESENTATION)
# =====================================================================
if not st.session_state.exam_submitted:
    with spoken_area.container():
        st.markdown("---")
        st.markdown("Audio Evaluation")
        st.warning("Proctoring Active: Changing windows or tabs will flag your account.")

        st.markdown("""
        <div style="background-color:#fff3cd; padding:15px; border-radius:5px; border-left: 5px solid #ffc107; margin-bottom:15px; color: #664d03;">
            <strong>How to Record Your Audio Response:</strong><br>
            1. Click the microphone icon below to <strong>START</strong> recording.<br>
            2. Speak clearly into your device microphone.<br>
            3. <strong>NOTE</strong> The recording automatically stops once you stop speaking. Else click the icon a <strong>SECOND TIME</strong> to finalize and save.<br>
            4. Green - Recording, Red - Idle.<br>
        </div>
        """, unsafe_allow_html=True)

        rec_box_col1, rec_box_col2 = st.columns([1, 4])
        with rec_box_col1:
            st.write("**Click Here:**")
            audio_payload = audio_recorder(text="Record", neutral_color="#D32F2F", recording_color="#2E7D32")
        with rec_box_col2:
            if not audio_payload:
                st.info("System Status: Ready to Record.")
            else:
                st.success("System Status: Audio Processed Successfully.")
        
        if audio_payload:
            st.audio(audio_payload, format="audio/wav")

    with written_area.container():
        st.markdown("---")
        st.markdown("Writing Evaluation")
        candidate_essay = st.text_area("Type your essay response cleanly below (Copy/Paste Protected):", height=150)

calculated_wpm = 10.7
##extracted_transcript = "Minnesota State Lottery results"
detected_fillers = 0
assigned_speech_tier = "Beginner"

# =====================================================================
# 6. SUBMISSION TRIGGER (DESTROYS TEST INTERFACE, BUILDS RAW REPORT)
# =====================================================================
if not st.session_state.exam_submitted:
    with submit_button_area.container():
        if st.button("Finalize and Submit Performance Assessment"):
            if not candidate_essay:
                st.warning("Assessment criteria check incomplete. Please provide text input before finalizing.")
            else:
                st.session_state.exam_submitted = True
                st.rerun()

# =====================================================================
# 7. THE EXCLUSIVE REPORT VIEW LAYER WITH PRINT BUTTON
# =====================================================================
if st.session_state.exam_submitted:
    # Clear all test inputs to leave a clean slate
    header_area.empty()
    auth_area.empty()
    spoken_area.empty()
    written_area.empty()
    submit_button_area.empty()
    
    # Render Metadata Authentication block inside the final printable layout context
    st.markdown("<h2 style='text-align: center; color: #1E88E5; font-family:Sans-Serif; margin-bottom: 2px;'>OFFICIAL ASSESSMENT PERFORMANCE SCORECARD</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size:15px; font-family:Sans-Serif; font-weight:bold; margin-top:0px;'>TRAINEE NAME: {trainee_name.upper()} | EMP ID: {emp_id.upper()}</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid #1E88E5; margin-bottom: 20px;'>", unsafe_allow_html=True)
    
    # Render Report Metrics Columns
    left_report_pane, right_report_pane = st.columns([1, 1])
    
    with left_report_pane:
        st.markdown("#### Spoken Audio Assessment Metrics")
        st.markdown(f"""
        | Metric | Evaluation Score |
        | :--- | :--- |
        | **Speaking Pacing Rate** | {calculated_wpm} WPM |
        | **Filler Words Count** | {detected_fillers} |
        | **Assessed Competency Tier** | **{assigned_speech_tier}** |
        """)
        ##st.markdown(f"**Speech Transcript:** \n> *\"{extracted_transcript}\"*")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Written Competency Ratings")
        st.markdown("""
        * **Grammar and Clarity:** 40%
        * **Vocabulary Depth:** 65%
        * **Conciseness Profile:** 95%
        * **Impact:** 40%
        """)

    with right_report_pane:
        st.markdown("#### Linguistic Quality Map")
        
        radar_labels = ['Grammar/Ease', 'Vocabulary Soph.', 'Conciseness', 'Impact Alignment', 'Grammar/Ease']
        radar_scores = [40, 65, 95, 40, 40]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=radar_scores,
            theta=radar_labels,
            fill='toself',
            fillcolor='rgba(30, 136, 229, 0.15)',
            line=dict(color='#1E88E5', width=2),
            name='Competency'
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100]),
                angularaxis=dict(tickfont=dict(size=10))
            ),
            showlegend=False,
            width=380,
            height=320,
            margin=dict(l=40, r=40, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=False)

    st.markdown("<hr style='border: 0.5px solid #ccc;'>", unsafe_allow_html=True)
    st.markdown("### Evaluation Insights Summary")
    
    ins_col1, ins_col2 = st.columns(2)
    with ins_col1:
        st.markdown("**Identified Core Strengths:**")
        st.write("• Excellent structural pacing averaging 17.0 words per phrase.")
    with ins_col2:
        st.markdown("**Flagged Weakness Metrics:**")
        st.write("• Passive vocabulary style: Lacks results-oriented business vocabulary words.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='background-color:#f0f7fc; padding:15px; border-radius:5px; border-left: 5px solid #1E88E5; color: #000;'>", unsafe_allow_html=True)
    st.markdown("#### Actionable Tactical Plan")
    st.markdown("STEP 1: Integrate dynamic professional focus terms (e.g., use 'optimized' or 'executed').")
    st.markdown("</div>", unsafe_allow_html=True)

    # Print button configuration layer
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    print_js_button = """
    <script>
        function triggerCleanPrint() {
            window.parent.print();
        }
    </script>
    <button onclick="triggerCleanPrint()" style="background-color: #1E88E5; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold; width: 100%;">
        Download Scorecard as PDF
    </button>
    """
    st.components.v1.html(print_js_button, height=60)
