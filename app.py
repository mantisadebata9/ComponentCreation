"""
Streamlit UI for Figma-to-Jutro Agent
"""
import streamlit as st
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from agent.figma_reader import FigmaReader
from agent.component_detector import ComponentDetector
from agent.jutro_mapper import JutroComponentMapper
from agent.code_generator import CodeGenerator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Figma-to-Jutro Agent",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.title("🎨 Figma-to-Jutro Agent")
    st.markdown("*Design-to-Code AI Agent for Guidewire Jutro Developers*")

    # Sidebar navigation
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Keys
        figma_api_key = st.text_input(
            "Figma API Key",
            type="password",
            help="Get from https://www.figma.com/developers"
        )
        
        openai_api_key = st.text_input(
            "OpenAI API Key (optional)",
            type="password",
            help="For advanced vision-based component detection"
        )

    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📥 Upload Design", "🔍 Preview", "💾 Export"])

    with tab1:
        st.header("Upload Design")
        st.markdown("Choose your input method:")

        input_type = st.radio(
            "Select input type:",
            ["Figma URL", "Upload .fig File", "Upload Image"],
            horizontal=True
        )

        if input_type == "Figma URL":
            figma_url = st.text_input(
                "Enter Figma URL",
                placeholder="https://www.figma.com/file/..."
            )
            if st.button("📥 Load from Figma"):
                process_figma_url(figma_url, figma_api_key)

        elif input_type == "Upload .fig File":
            fig_file = st.file_uploader("Choose .fig file", type=["fig"])
            if fig_file:
                process_fig_file(fig_file)

        else:  # Upload Image
            image_file = st.file_uploader(
                "Choose image",
                type=["png", "jpg", "jpeg"]
            )
            if image_file:
                process_image(image_file, openai_api_key)

    with tab2:
        st.header("Preview Generated Components")
        
        if 'design' not in st.session_state:
            st.info("Upload a design first")
        else:
            preview_generated_code()

    with tab3:
        st.header("Export Generated Code")
        
        if 'generated_files' not in st.session_state:
            st.info("Generate components first")
        else:
            export_code()


def process_figma_url(figma_url: str, api_key: str):
    """Process Figma URL"""
    if not figma_url:
        st.error("Please enter a Figma URL")
        return

    if not api_key:
        st.error("Please provide Figma API Key")
        return

    try:
        with st.spinner("Reading Figma design..."):
            reader = FigmaReader(api_key=api_key)
            design = reader.read_from_url(figma_url)

        st.session_state.design = design
        st.success(f"✅ Loaded design: {design.project_name}")
        st.info(f"Found {len(design.frames)} frames")

        # Detect components
        detect_and_map_components(design)

    except Exception as e:
        st.error(f"Error: {str(e)}")


def process_fig_file(uploaded_file):
    """Process uploaded .fig file"""
    import tempfile
    import os

    try:
        with st.spinner("Reading .fig file..."):
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.fig') as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            reader = FigmaReader()
            design = reader.read_from_file(tmp_path)

            # Clean up
            os.remove(tmp_path)

        st.session_state.design = design
        st.success(f"✅ Loaded design: {design.project_name}")
        st.info(f"Found {len(design.frames)} frames")

        # Detect components
        detect_and_map_components(design)

    except Exception as e:
        st.error(f"Error: {str(e)}")


def process_image(uploaded_file, api_key: str):
    """Process uploaded image"""
    try:
        with st.spinner("Analyzing image..."):
            # Display image
            st.image(uploaded_file, caption="Uploaded Design", use_column_width=True)

            # For now, show placeholder
            st.info("Image processing coming soon with vision-based component detection")

    except Exception as e:
        st.error(f"Error: {str(e)}")


def detect_and_map_components(design):
    """Detect and map components"""
    try:
        with st.spinner("Detecting components..."):
            detector = ComponentDetector()
            
            # Process first frame
            if design.frames:
                first_frame = design.frames[0]
                components = detector.detect_from_frame(first_frame.properties)
                
                # Map to Jutro
                mapper = JutroComponentMapper()
                mapped = mapper.map_frame(components)

                st.session_state.components = components
                st.session_state.mapped_components = mapped

                # Generate code
                with st.spinner("Generating code..."):
                    generator = CodeGenerator()
                    page_file = generator.generate_page(
                        first_frame.name,
                        mapped['components']
                    )
                    st.session_state.generated_files = [page_file]

                st.success("✅ Components detected and mapped!")

    except Exception as e:
        st.error(f"Error: {str(e)}")


def preview_generated_code():
    """Show preview of generated code"""
    if 'mapped_components' not in st.session_state:
        st.info("No components detected")
        return

    mapped = st.session_state.mapped_components
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Detected Components")
        for component in mapped['components']:
            with st.expander(f"📦 {component['figma_name']}"):
                st.write(f"**Type:** {component['figma_type']}")
                st.write(f"**Jutro Component:** `{component['jutro_component']}`")
                st.write(f"**Confidence:** {component['confidence']:.0%}")
                st.json(component['props'])

    with col2:
        st.subheader("Generated Code")
        if st.session_state.generated_files:
            with open(st.session_state.generated_files[0], 'r') as f:
                code = f.read()
            st.code(code, language='typescript')


def export_code():
    """Export generated code"""
    if 'generated_files' not in st.session_state:
        st.info("No files generated")
        return

    st.subheader("Generated Files")
    for file_path in st.session_state.generated_files:
        with open(file_path, 'r') as f:
            code = f.read()

        filename = Path(file_path).name
        st.download_button(
            label=f"📥 Download {filename}",
            data=code,
            file_name=filename,
            mime="text/typescript"
        )


if __name__ == "__main__":
    main()