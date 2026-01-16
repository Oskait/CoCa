import streamlit as st
import database as db

# --- Page Configuration ---
st.set_page_config(
    page_title="Dilution Calculator",
    page_icon="🧪",
    layout="centered",
)

# --- Database Initialization ---
db.init_db()

# --- Functions ---
def calculate_mass(molar_concentration_mM, volume_ml, molecular_weight):
    """Calculates the mass in grams required."""
    if molecular_weight is None or molecular_weight == 0:
        return 0
    molar_concentration_M = molar_concentration_mM / 1000.0
    volume_l = volume_ml / 1000.0
    mass = molar_concentration_M * volume_l * molecular_weight
    return mass

def calculate_volume(mass_g, molar_concentration_mM, molecular_weight):
    """Calculates the volume in mL required for a given mass."""
    if molecular_weight is None or molecular_weight == 0 or molar_concentration_mM == 0:
        return 0
    molar_concentration_M = molar_concentration_mM / 1000.0
    volume_l = (mass_g / molecular_weight) / molar_concentration_M
    volume_ml = volume_l * 1000.0
    return volume_ml

# --- App Title ---
st.title("🧪 Dilution Calculator")
#st.markdown("Quick dilution calculations.")

# --- Step 1: Compound Selection ---
#st.subheader("Select Compound")

all_compounds = db.get_all_compounds()
molecular_weight = None

if not all_compounds:
    st.warning("No compounds in database. Use the Compound Manager to add some.")
    st.stop()

compound_map = {c['shortname']: c for c in all_compounds}

# Pad shortnames for aligned display in the selectbox
max_len = max(len(s) for s in compound_map.keys()) if compound_map else 0
nbsp = " " # Non-breaking space character

display_map = {}
for c in all_compounds:
    shortname = c['shortname']
    longname = c['longname']
    # Use ljust for alignment and add non-breaking spaces for a clear gap
    padded_shortname = shortname.ljust(max_len)
    
    display_name = padded_shortname
    if longname and longname != shortname:
        display_name += f"{nbsp*4}({longname})"
    display_map[shortname] = display_name

display_names = list(display_map.values())
shortname_map = {v: k for k, v in display_map.items()}

# --- Session State & Callback ---
def _compound_changed():
    """Update state when a new compound is selected."""
    selected_shortname = shortname_map[st.session_state.selected_compound_key]
    compound_data = compound_map[selected_shortname]
    st.session_state.desired_conc_mM = float(compound_data.get('standard_concentration') or 0.0)
    st.session_state.desired_volume_ml = float(compound_data.get('standard_volume') or 0.0)

# Initialize state if it's not already set
if 'selected_compound_key' not in st.session_state:
    st.session_state.selected_compound_key = display_names[0]
    _compound_changed() # Manually call to set initial conc/vol

selected_display_name = st.selectbox(
    "Select Compound:",
    options=display_names,
    key='selected_compound_key',
    on_change=_compound_changed
)

selected_shortname = shortname_map[selected_display_name]
compound_data = compound_map[selected_shortname]
molecular_weight = compound_data.get('molecular_weight')

if molecular_weight is not None:
    st.info(f"MW of **{selected_shortname}**: `{molecular_weight:.4f} g/mol`")
else:
    st.error("Could not retrieve data for the selected compound.")
    st.stop()

# --- Step 2: Define Desired Solution ---
#st.subheader("Define Solution")

col1, col2 = st.columns(2)
with col1:
    # Determine format based on the current value in session state
    current_conc = st.session_state.get('desired_conc_mM', 0.0)
    try:
        # Use a small tolerance for float comparison
        is_integer = abs(current_conc - round(current_conc)) < 1e-9
    except TypeError:
        is_integer = False
        
    conc_format = "%.0f" if is_integer else "%.6f"
    
    desired_concentration = st.number_input(
        "Target Conc. (mM)",
        min_value=0.0,
        format=conc_format,
        key='desired_conc_mM',
        help="Molar concentration in millimolar (mmol/L)"
    )
    if desired_concentration > 0:
        st.caption(f"{desired_concentration / 1000.0:g} M")

with col2:
    current_vol = st.session_state.get('desired_volume_ml', 0.0)
    try:
        is_vol_integer = abs(current_vol - round(current_vol)) < 1e-9
    except TypeError:
        is_vol_integer = False

    vol_format = "%.0f" if is_vol_integer else "%.2f"

    desired_volume = st.number_input(
        "Target Volume (mL)",
        min_value=0.0,
        format=vol_format,
        key='desired_volume_ml'
    )

# --- Step 3 & 4: Mass and Volume Adjustment ---
col3, col4 = st.columns(2)

with col3:
#    st.subheader("Calculate Mass")
    # Initialize state for calculated and actual mass
    if 'calculated_mass' not in st.session_state:
        st.session_state.calculated_mass = 0.0
    if 'actual_mass_mg' not in st.session_state:
        st.session_state.actual_mass_mg = 0.0

    if molecular_weight and desired_concentration > 0 and desired_volume > 0:
        st.session_state.calculated_mass = calculate_mass(desired_concentration, desired_volume, molecular_weight)
        st.metric(
            label="Required Mass:",
            value=f"{st.session_state.calculated_mass * 1000:.2f} mg",
            delta=f"({st.session_state.calculated_mass:.4f} g)"
        )
    else:
        st.info("Complete steps above to calculate required mass.")
        st.session_state.calculated_mass = 0.0

with col4:
#    st.subheader("Adjust for Actual Mass")
    # Auto-update actual mass from calculated mass only once
    if st.session_state.calculated_mass > 0 and st.session_state.actual_mass_mg == 0.0:
        st.session_state.actual_mass_mg = st.session_state.calculated_mass * 1000

    actual_mass_mg = st.number_input(
        "Weigh-in (mg)",
        min_value=0.0,
        format="%.2f",
        key='actual_mass_mg',
        help="Enter the exact mass you weighed in milligrams. The required volume will update automatically."
    )

    if actual_mass_mg > 0 and molecular_weight and desired_concentration > 0:
        actual_mass_g = actual_mass_mg / 1000.0
        final_volume = calculate_volume(actual_mass_g, desired_concentration, molecular_weight)
        st.metric(
            label="Volume to Add:",
            value=f"{final_volume:.2f} mL",
            delta=f"{final_volume * 1000:.0f} µL"
        )
    else:
        st.info("Final volume will be calculated once actual mass is entered.")

# --- Footer ---
st.markdown("---")
st.markdown("Made with ❤️ for the lab.")
