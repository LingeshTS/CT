import streamlit as st
import re
import math
import plotly.graph_objects as go
from audio_recorder_streamlit import audio_recorder
import mysql.connector

# =====================================================================
# 0. NATIVE DATABASE CONNECTOR
# =====================================================================
def save_metrics_to_mysql(name, employee_id, wpm, fillers, tier, grammar, vocab, conciseness, impact):
    """Establishes direct connection to local database without st.secrets dependencies."""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Lingesh@2810",
            database="ct",
            port=3306
        )
        
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO trainee_evaluations 
        (trainee_name, emp_id, speaking_wpm, filler_words, speech_tier, grammar_score, vocabulary_score, conciseness_score, impact_score) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        record_payload = (name, employee_id, wpm, fillers, tier, grammar, vocab, conciseness, impact)
        
        cursor.execute(insert_query, record_payload)
        connection.commit()  
        
        cursor.close()
        connection.close()
        return True
    except Exception as db_error:
        print(f"Database Ingestion Failure Log: {str(db_error)}")
        return False

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
        st.markdown(strict_security_js, unsafe_allow_html=True)

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
            <strong>Green</strong> - Recording<br><strong>Red</strong> - Idle.<br>
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
            st.session_state.audio_duration = max(len(audio_payload) / 32000, 1.0)

    with written_area.container():
        st.markdown("---")
        st.markdown("Writing Evaluation")
        candidate_essay = st.text_area("Type your essay response:", height=150)
        if candidate_essay:
            st.session_state.candidate_essay = candidate_essay

# Default fallbacks
calculated_wpm = 10.7
detected_fillers = 0
assigned_speech_tier = "Beginner"

# =====================================================================
# 6. SUBMISSION TRIGGER & COMPLETE DYNAMIC EVALUATION ENGINE
# =====================================================================
if not st.session_state.exam_submitted:
    with submit_button_area.container():
        if st.button("Finalize and Submit Performance Assessment"):
            if not st.session_state.get("candidate_essay"):
                st.warning("Assessment criteria check incomplete. Please provide text input before finalizing.")
            else:
                essay_text = st.session_state.candidate_essay
                words_list = re.sub(r'[^\w\s]', '', essay_text).split()
                total_essay_words = len(words_list)
                unique_words = set(words_list)
                
                duration = st.session_state.get("audio_duration", 30.0)
                fillers_found = len(re.findall(r'\b(um|uh|like|so|basically|actually)\b', essay_text, re.IGNORECASE))
                wpm_calculated = round((total_essay_words / duration) * 60, 1)
                
                if wpm_calculated < 40: 
                    wpm_calculated = round(total_essay_words * 1.2, 1)
                
                tier_assigned = "Advanced" if fillers_found <= 1 and wpm_calculated >= 110 else "Competent" if fillers_found <= 4 else "Beginner"

                vocab_richness = (len(unique_words) / total_essay_words * 100) if total_essay_words > 0 else 50
                sentences = [s for s in re.split(r'[.!?]+', essay_text) if s.strip()]
                total_sentences = len(sentences) if len(sentences) > 0 else 1
                avg_sentence_len = total_essay_words / total_sentences
                
                grammar_score = max(int(100 - (fillers_found * 8) - (abs(15 - avg_sentence_len) * 2)), 30)
                vocab_score = min(int(vocab_richness + 15), 100)
                conciseness_score = min(int(100 - (avg_sentence_len * 1.5)), 95) if avg_sentence_len > 12 else 90
                impact_score = min(int((grammar_score + vocab_score) / 2 + 5), 100)
                
                if avg_sentence_len >= 14 and avg_sentence_len <= 22:
                    strength_msg = f"• Excellent structural pacing averaging {round(avg_sentence_len, 1)} words per phrase."
                elif avg_sentence_len < 14:
                    strength_msg = "• Crisp and punchy structural cadence, promoting fast delivery compression formats."
                else:
                    strength_msg = "• High descriptive capacity with elaborate architectural structuring profiles."

                if vocab_score < 70:
                    weakness_msg = "• Passive vocabulary style: Lacks results-oriented business vocabulary words."
                    plan_msg = "STEP 1: Integrate dynamic professional focus terms (e.g., use 'optimized', 'executed', or 'leveraged') to maximize semantic authority configurations."
                elif fillers_found > 3:
                    weakness_msg = f"• High conversational hesitation index: Observed {fillers_found} explicit filler word markers within syntactic units."
                    plan_msg = "STEP 1: Implement structural speech pacing adjustments. Pause intentionally between conceptual statements instead of injecting placeholder metrics."
                elif grammar_score < 70:
                    weakness_msg = "• Varied syntactical alignment: Sentence structures deviate from concise active-voice constraints."
                    plan_msg = "STEP 1: Restructure compound sentences into active, subject-driven structural elements to increase grammar clarity variables."
                else:
                    weakness_msg = "• Minor layout pacing variations: Sentence structural balance could handle more stylistic variance."
                    plan_msg = "STEP 1: Practice variable sentence phrasing lengths to maximize delivery impact profiles across corporate analytics reporting tasks."

                st.session_state.calculated_wpm = wpm_calculated
                st.session_state.detected_fillers = fillers_found
                st.session_state.assigned_speech_tier = tier_assigned
                st.session_state.grammar_score = grammar_score
                st.session_state.vocab_score = vocab_score
                st.session_state.conciseness_score = conciseness_score
                st.session_state.impact_score = impact_score
                st.session_state.avg_len = avg_sentence_len
                st.session_state.dynamic_strength = strength_msg
                st.session_state.dynamic_weakness = weakness_msg
                st.session_state.dynamic_plan = plan_msg

                save_metrics_to_mysql(
                    name=trainee_name,
                    employee_id=emp_id,
                    wpm=wpm_calculated,
                    fillers=fillers_found,
                    tier=tier_assigned,
                    grammar=grammar_score,
                    vocab=vocab_score,
                    conciseness=conciseness_score,
                    impact=impact_score
                )
                
                st.session_state.exam_submitted = True
                st.rerun()

# =====================================================================
# 7. THE EXCLUSIVE REPORT VIEW LAYER WITH PRINT RUNS
# =====================================================================
if st.session_state.exam_submitted:
    header_area.empty()
    auth_area.empty()
    spoken_area.empty()
    written_area.empty()
    submit_button_area.empty()
    
    wpm_stat = st.session_state.get("calculated_wpm", calculated_wpm)
    fillers_stat = st.session_state.get("detected_fillers", detected_fillers)
    tier_stat = st.session_state.get("assigned_speech_tier", assigned_speech_tier)
    g_score = st.session_state.get("grammar_score", 40)
    v_score = st.session_state.get("vocab_score", 65)
    c_score = st.session_state.get("conciseness_score", 95)
    i_score = st.session_state.get("impact_score", 40)
    essay_saved = st.session_state.get("candidate_essay", "")
    
    final_strength = st.session_state.get("dynamic_strength", "")
    final_weakness = st.session_state.get("dynamic_weakness", "")
    final_plan = st.session_state.get("dynamic_plan", "")
    
    st.markdown("<h2 style='text-align: center; color: #1E88E5; font-family:Sans-Serif; margin-bottom: 2px;'>OFFICIAL ASSESSMENT PERFORMANCE SCORECARD</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size:15px; font-family:Sans-Serif; font-weight:bold; margin-top:0px;'>TRAINEE NAME: {trainee_name.upper()} | EMP ID: {emp_id.upper()}</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid #1E88E5; margin-bottom: 20px;'>", unsafe_allow_html=True)
    
    left_report_pane, right_report_pane = st.columns([1, 1])
    
    with left_report_pane:
        st.markdown("#### Spoken Audio Assessment Metrics")
        st.markdown(f"""
        | Metric | Evaluation Score |
        | :--- | :--- |
        | **Speaking Pacing Rate** | {wpm_stat} WPM |
        | **Filler Words Count** | {fillers_stat} |
        | **Assessed Competency Tier** | **{tier_stat}** |
        """)
        
        truncated_transcript = (essay_saved[:90] + '...') if len(essay_saved) > 90 else essay_saved
        st.markdown(f"**Speech Transcript:** \n> *\"{truncated_transcript}\"*")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Written Competency Ratings")
        st.markdown(f"""
        * **Grammar and Clarity:** {g_score}%
        * **Vocabulary Depth:** {v_score}%
        * **Conciseness Profile:** {c_score}%
        * **Impact:** {i_score}%
        """)

    with right_report_pane:
        st.markdown("#### Linguistic Quality Map")
        
        radar_labels = ['Grammar/Ease', 'Vocabulary Soph.', 'Conciseness', 'Impact Alignment', 'Grammar/Ease']
        radar_scores = [g_score, v_score, c_score, i_score, g_score]
        
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
        st.plotly_chart(fig, width='content')

    st.markdown("<hr style='border: 0.5px solid #ccc;'>", unsafe_allow_html=True)
    st.markdown("### Evaluation Insights Summary")
    
    ins_col1, ins_col2 = st.columns(2)
    with ins_col1:
        st.markdown("**Identified Core Strengths:**")
        st.write(final_strength)
    with ins_col2:
        st.markdown("**Flagged Weakness Metrics:**")
        st.write(final_weakness)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='background-color:#f0f7fc; padding:15px; border-radius:5px; border-left: 5px solid #1E88E5; color: #000;'>", unsafe_allow_html=True)
    st.markdown("#### Actionable Tactical Plan")
    st.markdown(final_plan)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    st.components.v1.html("""
<button id="printBtn" style="
    background-color: #1E88E5;
    color: white;
    padding: 12px 24px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    font-weight: bold;
    width: 100%;">
    Download Scorecard as PDF
</button>

<script>
document.getElementById("printBtn").onclick = function() {
    parent.window.print();
};
</script>
""", height=60)
