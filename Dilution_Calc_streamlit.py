import streamlit as st
import database as db

# --- Page Configuration ---
st.set_page_config(
    page_title="Dilution Calculator",
    page_icon="🧪",
    layout="centered",  # Use "centered" for a more compact, mobile-friendly view
)

# --- Database Initialization ---
db.init_db()

# --- Functions ---
def calculate_mass(molar_concentration, volume_ml, molecular_weight):
    """Calculates the mass in grams required."""
    if molecular_weight is None or molecular_weight == 0:
        return 0
    volume_l = volume_ml / 1000.0
    mass = molar_concentration * volume_l * molecular_weight
    return mass

def calculate_volume(mass_g, molar_concentration, molecular_weight):
    """Calculates the volume in mL required for a given mass."""
    if molecular_weight is None or molecular_weight == 0 or molar_concentration == 0:
        return 0
    volume_l = (mass_g / molecular_weight) / molar_concentration
    volume_ml = volume_l * 1000.0
    return volume_ml

# --- App Title ---
st.title("🧪 Dilution Calculator")
st.markdown("Designed for quick calculations on your phone.")

# --- Session State Initialization ---
# To hold values between reruns
if 'actual_mass' not in st.session_state:
    st.session_state.actual_mass = 0.0
if 'calculated_mass' not in st.session_state:
    st.session_state.calculated_mass = 0.0

# --- Step 1: Compound Selection ---
st.header("Step 1: Select Compound")

compounds = db.get_all_compound_names()
compound_data = None
molecular_weight = None

if not compounds:
    st.warning("No compounds found in the database. Please add compounds manually to the `compounds.db` file.")
    # Stop the app from processing further if no compounds are available
    st.stop()

selected_compound_name = st.selectbox(
    "Select a compound from the database:",
    options=compounds,
    index=0
)

if selected_compound_name:
    compound_data = db.get_compound(selected_compound_name)

if compound_data:
    molecular_weight = compound_data.get('molecular_weight')
    if molecular_weight is not None:
        st.info(f"Molecular Weight of **{selected_compound_name}**: `{molecular_weight:.4f} g/mol`")
else:
    st.error("Could not retrieve data for the selected compound.")
    st.stop()


# --- Step 2: Define Desired Solution ---
st.header("Step 2: Define Desired Solution")

# Get standard values from the compound data, with fallbacks to 0.0
default_concentration = compound_data.get('standard_concentration') or 0.0
default_volume = compound_data.get('standard_volume') or 0.0

col1, col2 = st.columns(2)
with col1:
    desired_concentration = st.number_input(
        "Desired Conc. (M)",
        min_value=0.0,
        value=float(default_concentration),
        format="%.6f",  # Increased precision for low concentrations
        help="Molar concentration (mol/L)"
    )
with col2:
    desired_volume = st.number_input(
        "Desired Volume (mL)",
        min_value=0.0,
        value=float(default_volume),
        format="%.2f"
    )

# --- Step 3: Initial Mass Calculation ---
st.header("Step 3: Calculate Required Mass")

if molecular_weight and desired_concentration > 0 and desired_volume > 0:
    st.session_state.calculated_mass = calculate_mass(desired_concentration, desired_volume, molecular_weight)
    st.metric(
        label="You will need to weigh out:",
        value=f"{st.session_state.calculated_mass * 1000:.2f} mg",
        delta=f"({st.session_state.calculated_mass:.4f} g)"
    )
else:
    st.info("Please complete the steps above to calculate the required mass.")
    st.session_state.calculated_mass = 0.0

# --- Step 4: Adjust for Actual Mass ---
st.header("Step 4: Adjust for Actual Mass")
st.markdown("Update the mass you actually weighed to get the precise volume needed.")

# Initialize the input with the calculated mass from the previous step
if st.session_state.calculated_mass > 0 and st.session_state.actual_mass == 0.0:
    st.session_state.actual_mass = st.session_state.calculated_mass

actual_mass_g = st.number_input(
    "Actual Weighed Mass (g)",
    min_value=0.0,
    format="%.4f",
    key='actual_mass',
    help="Enter the exact mass you weighed. The required volume will update automatically."
)

if actual_mass_g > 0 and molecular_weight and desired_concentration > 0:
    final_volume = calculate_volume(actual_mass_g, desired_concentration, molecular_weight)
    st.metric(
        label="Volume to add for desired concentration:",
        value=f"{final_volume:.2f} mL"
    )
else:
    st.info("The final volume will be calculated once an actual mass is entered.")

# --- Footer ---
st.markdown("---")
st.markdown("Made with ❤️ for the lab.")
