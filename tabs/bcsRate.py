import streamlit as st
import google.generativeai as genai
import base64
from PIL import Image
from dotenv import load_dotenv
import os
import io


st.session_state.update(st.session_state)
def show():
    # Load environment variables
    load_dotenv()

    # Configure Gemini API
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    model = genai.GenerativeModel("gemini-1.5-pro")

    CATTLE_ANALYSIS_PROMPT = """You are evaluating cattle images with multiple references:
    1. First image: BCS 1 (Emaciated) reference
    2. Second image: BCS 5 (Ideal) reference
    3. Third image: BCS 7 (Moderately Obese) reference
    4. Fourth image: BCS 9 (Obese) reference
    5. Fifth image: Conformation reference standard
    6. Final image: Subject cattle to be evaluated

    Using these reference standards, provide a detailed analysis:

    BODY CONDITION SCORE:
    Compare the subject directly to the BCS references (1, 5, and 9) considering:
    - Ribs and rib coverage
    - Tail head and fat deposits
    - Pin bones visibility and cover
    - Hook bones visibility
    - Shoulder blade coverage
    - Brisket fullness
    - Backbone/spine visibility
    - Transverse Process visibility

    Describe specifically how the subject compares to each reference image to justify your final BCS score.

    COMPETITIVE JUDGING CRITERIA:
    Compare to the conformation reference and evaluate:

    I. Frame & Structural Correctness (30 Points)
    A. Frame Size and Scale (10 points):
    - Height at hooks and withers
    - Length of body from shoulder to pins
    - Overall proportion relative to age
    - Width and substance of frame

    B. Structural Correctness (20 points):
    - Front End: shoulder angle, leg placement, pasterns
    - Rear Legs: hock set, joint cleanliness, pastern strength
    - Topline: level from hooks to pins, back strength

    II. Muscling and Volume (30 Points)
    A. Muscle Expression (15 points):
    - Forearm muscling
    - Width/depth through stifle
    - Quarter expression
    - Shoulder definition
    - Center body thickness

    B. Volume and Capacity (15 points):
    - Heart girth
    - Spring of rib
    - Body depth
    - Barrel capacity

    III. Balance and Style (20 Points)
    - Front-to-rear balance
    - Top-to-bottom balance
    - Smoothness between parts
    - Overall style and presence

    IV. Production Traits (20 Points)
    - Growth and performance indicators
    - Reproductive trait indicators
    - Breed characteristics

    Be extremely critical and specific in your evaluation. Point out specific flaws, superiorities, and differences from each reference animal. Use precise anatomical terminology and explain how each feature impacts functionality and value.

    Format your response as:

    BODY CONDITION SCORE ANALYSIS:
    Comparison to BCS 1 Reference:
    [Details]

    Comparison to BCS 5 Reference:
    [Details]

    Comparison to BCS 7 Reference:
    [Details]

    Comparison to BCS 9 Reference:
    [Details]

    Final BCS Score: [1-9]
    [Detailed justification]

    COMPETITIVE JUDGING EVALUATION:
    Frame & Structural Correctness: [X/30]
    [Detailed critical analysis]

    Muscling and Volume: [X/30]
    [Detailed critical analysis]

    Balance and Style: [X/20]
    [Detailed critical analysis]

    Production Traits: [X/20]
    [Detailed critical analysis]

    TOTAL SCORE: [X/100]

    FINAL ASSESSMENT:
    [Critical comparison to reference animals]
    [Major strengths]
    [Major weaknesses]
    [Placement recommendation in a show setting]"""

    def process_image(image):
        """Process PIL Image for Gemini API"""
        # Convert RGBA to RGB if needed
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if image is too large
        max_size = 1024
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image

    
    st.title("Phenotypical Cattle Evaluation System")
    
    # Check for API key
    if not os.getenv('GOOGLE_API_KEY'):
        st.error("Google API key not found! Please set it in your .env file.")
        st.stop()
    
    # Add reference image uploads to sidebar
    with st.sidebar:
        with st.expander("Reference Images"):
            st.subheader("BCS Reference Standards")
            bcs1_file = st.file_uploader("Upload BCS 1 (Emaciated)", type=['jpg', 'jpeg', 'png'])
            if bcs1_file:
                bcs1_image = Image.open(bcs1_file)
                st.image(bcs1_image, caption="BCS 1 Reference", use_container_width=True)
                
            st.divider()
            
            bcs5_file = st.file_uploader("Upload BCS 5 (Ideal)", type=['jpg', 'jpeg', 'png'])
            if bcs5_file:
                bcs5_image = Image.open(bcs5_file)
                st.image(bcs5_image, caption="BCS 5 Reference", use_container_width=True)
                
            st.divider()
            
            bcs7_file = st.file_uploader("Upload BCS 7 (Moderately Obese)", type=['jpg', 'jpeg', 'png'])
            if bcs7_file:
                bcs7_image = Image.open(bcs7_file)
                st.image(bcs7_image, caption="BCS 7 Reference", use_container_width=True)
                
            st.divider()
            
            bcs9_file = st.file_uploader("Upload BCS 9 (Obese)", type=['jpg', 'jpeg', 'png'])
            if bcs9_file:
                bcs9_image = Image.open(bcs9_file)
                st.image(bcs9_image, caption="BCS 9 Reference", use_container_width=True)
                
            st.divider()
            
            st.subheader("Conformation Reference")
            conf_file = st.file_uploader("Upload conformation standard", type=['jpg', 'jpeg', 'png'])
            if conf_file:
                conf_image = Image.open(conf_file)
                st.image(conf_image, caption="Conformation Reference", use_container_width=True)
        
    # Main area for subject evaluation
    st.write("""
    ### Competition-Level Cattle Evaluation Tool
    Upload reference images in the sidebar and the subject to be evaluated below.
    """)
    
    st.subheader("Subject Evaluation")
    subject_file = st.file_uploader("Upload subject to evaluate", type=['jpg', 'jpeg', 'png'])
    if subject_file:
        subject_image = Image.open(subject_file)
        st.image(subject_image, caption="Subject for Evaluation", use_container_width=True)
    
    if all([bcs1_file, bcs5_file, bcs7_file, bcs9_file, conf_file, subject_file]):
        if st.button("Perform Detailed Evaluation"):
            with st.spinner("Conducting comprehensive analysis..."):
                try:
                    # Process all images for Gemini
                    bcs1_processed = process_image(bcs1_image)
                    bcs5_processed = process_image(bcs5_image)
                    bcs7_processed = process_image(bcs7_image)
                    bcs9_processed = process_image(bcs9_image)
                    conf_processed = process_image(conf_image)
                    subject_processed = process_image(subject_image)
                    
                    # Create contents array for Gemini
                    contents = [
                        CATTLE_ANALYSIS_PROMPT,
                        bcs1_processed,
                        bcs5_processed,
                        bcs7_processed,
                        bcs9_processed,
                        conf_processed,
                        subject_processed
                    ]
                    
                    # Generate response from Gemini
                    response = model.generate_content(contents)
                    
                    # Display formatted results
                    st.subheader("Professional Evaluation Results")
                    
                    # Split and format the analysis sections
                    sections = response.text.split('\n\n')
                    for section in sections:
                        if "BCS Score:" in section:
                            st.warning(section)
                        elif any(score_type in section.upper() for score_type in ['SCORE:', 'TOTAL SCORE:', '/100', '/30', '/20']):
                            st.info(section)
                        elif 'FINAL ASSESSMENT:' in section.upper():
                            st.error(section)
                        else:
                            st.write(section)
                    
                    # Expandable section for raw analysis
                    with st.expander("View Complete Analysis"):
                        st.code(response.text)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    with st.expander("Error Details"):
                        st.write(e)
                        import traceback
                        st.code(traceback.format_exc())

