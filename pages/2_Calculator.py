# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import plotly.express as px
# from reportlab.lib.pagesizes import A4 # PDF generation commented out
# from reportlab.pdfgen import canvas    # PDF generation commented out
# from reportlab.lib.units import cm     # PDF generation commented out
from io import BytesIO
import traceback

# --- App Config ---
st.set_page_config(page_title="GreenPrint", page_icon="🌿", layout="centered")


st.markdown("""
    <style>
        /* --- Sidebar Logo --- */
        [data-testid="stSidebar"]::before {
            content: ""; display: block;
            background-image: url('https://raw.githubusercontent.com/GhazalMoradi8/Carbon_Footprint_Calculator/main/GreenPrint_logo.png');
            background-size: 90% auto; background-repeat: no-repeat;
            background-position: center; height: 140px;
            margin: 1.5rem auto -4rem auto;
        }
        section[data-testid="stSidebar"] { background-color: #d6f5ec; }
        .stApp { background-color: white; }

        /* --- Tab-like Radio Buttons --- */
        div[role="radiogroup"] > label > div:first-child { display: none; }
        div[role="radiogroup"] > label {
            margin: 0 !important; padding: 0.5rem 1rem; border: 1px solid #ddd;
            border-bottom: none; border-radius: 5px 5px 0 0; background-color: #f0f2f6;
            cursor: pointer; transition: background-color 0.3s ease;
        }
        div[role="radiogroup"] > label:hover { background-color: #e0e2e6; }

        /* --- Control the color of the selected tab --- */
        div[role="radiogroup"] input[type="radio"]:checked + label {
            background-color: #f0f2f6;
            font-weight: bold;
            color: #52a58a;  /* Change the color of selected tab text (Green in this case) */
        }

        /* --- Add bottom border for tabs container --- */
        div.stRadio > div {
            border-bottom: 1px solid #ddd;
            padding-bottom: 1rem;
        }

        /* --- Styling for the Next and Previous buttons --- */
        div[data-testid="stButton"] button {
            background-color: #61c2a2;  /* Green background */
            color: white;              /* White text */
            border: none;
            padding: 0.5rem 1rem;      /* Adjust padding */
            border-radius: 0.25rem;
        }
        div[data-testid="stButton"] button:hover {
            background-color: #52a58a;  /* Darker green on hover */
        }

        /* Focus state for buttons */
        div[data-testid="stButton"] button:focus {
            outline: none;  /* Remove the default focus outline */
            box-shadow: 0 0 0 0.3rem rgba(26, 152, 80, 0.5); /* Green shadow on focus */
        }

    </style>
""", unsafe_allow_html=True)



# --- Initialize Session State Variables ---
def init_session_state():
    defaults = {
        "selected_country": "-- Select --",
        "current_tab_index": 0,
        "emission_values": {},
        "calculation_done": False,
        "calculated_emission": None,
        "comparison_plot_data": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Load Emission Data ---
CSV_URL = "https://drive.google.com/uc?export=download&id=1PWeBZKB6adZKORvtMDLFwCX__gfzH33g"
PER_CAPITA_URL = "https://raw.githubusercontent.com/keanyaoha/Final_Project_WBS/main/per_capita_filtered_monthly.csv"

@st.cache_data
def load_data(csv_url, per_capita_url):
    try:
        df_emis = pd.read_csv(csv_url)
        df_cap = pd.read_csv(per_capita_url)
        df_emis.columns = df_emis.columns.str.strip()
        if 'Activity' not in df_emis.columns:
             st.error("Emission data CSV is missing 'Activity' column.")
             return None, None
        return df_emis, df_cap
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

df, df1 = load_data(CSV_URL, PER_CAPITA_URL)

if df is None or df1 is None:
    st.warning("Data loading failed. App cannot continue.")
    st.stop()

available_countries = sorted([col for col in df.columns if col != "Activity"])

# --- Format Activity Titles ---
def format_activity_name(activity_key):
    mapping = {
        "Domestic_flight_traveled": "Domestic Flights (km)", "International_flight_traveled": "International Flights (km)",
        "km_diesel_local_passenger_train_traveled": "Diesel Local Train (km)", "km_diesel_long_distance_passenger_train_traveled": "Diesel Long-Dist Train (km)",
        "km_electric_passenger_train_traveled": "Electric Train (km)", "km_bus_traveled": "Bus (km)",
        "km_petrol_car_traveled": "Petrol Car (km)", "km_Motorcycle_traveled": "Motorcycle (km)",
        "km_ev_scooter_traveled": "E-Scooter (km)", "km_ev_car_traveled": "Electric Car (km)",
        "diesel_car_traveled": "Diesel Car (km)", "beef_products_consumed": "Beef Products (euro)",
        "poultry_products_consumed": "Poultry Products (euro)", "pork_products_consumed": "Pork Products (euro)",
        "fish_products_consumed": "Fish Products (euro)", "other_meat_products_consumed": "Other Meat (euro)",
        "processed_rice_consumed": "Rice (euro)", "sugar_consumed": "Sugar (euro)",
        "vegetable_oils_fats_consumed": "Veg Oils/Fats (euro)", "dairy_products_consumed": "Dairy Products (euro)",
        "other_food_products_consumed": "Other Food (euro)", "water_consumed": "Water Consumed (m3)",
        "electricity_used": "Electricity Used (kWh)", "hotel_stay": "Hotel Nights (room-night)",
    }
    return mapping.get(activity_key, activity_key.replace("_", " ").capitalize())

# --- App Title ---
st.title("🌍 Carbon Footprint Calculator")
st.markdown("Estimate your monthly carbon footprint and compare it to country and global averages.")


# --- Country Selection ---
st.markdown("**Select your country**")
country_options = ["-- Select --"] + available_countries
current_selection = st.session_state.selected_country
if current_selection not in country_options:
    current_selection = "-- Select --"
    st.session_state.selected_country = current_selection

selected_country_widget = st.selectbox(
    label="country_select_hidden", label_visibility="collapsed",
    options=country_options, index=country_options.index(current_selection),
    key="country_selector_main"
)

# --- Update Session State on Country Change ---
if selected_country_widget != st.session_state.selected_country:
    st.session_state.selected_country = selected_country_widget
    st.session_state.current_tab_index = 0
    st.session_state.emission_values = {}
    st.session_state.calculation_done = False
    st.session_state.calculated_emission = None
    st.session_state.comparison_plot_data = None
    st.rerun()

# --- Main Content Area ---
if st.session_state.selected_country != "-- Select --":
    country = st.session_state.selected_country
    st.markdown("**Enter your monthly consumption details**")

    tab_labels = ["🚗 Transport", "🍽️ Food", " ⚡💧 Energy & Water", "🏨 Hotel"]
    selected_tab_label = st.radio(
        "Select Category:", tab_labels, index=st.session_state.current_tab_index,
        key="tab_selector", horizontal=True, label_visibility="collapsed"
    )

    clicked_index = tab_labels.index(selected_tab_label)
    if clicked_index != st.session_state.current_tab_index:
        st.session_state.current_tab_index = clicked_index
        st.rerun()

    def display_activity_inputs(activities, category_key, current_country):
        if not isinstance(activities, list): return
        for activity in activities:
            label = format_activity_name(activity)
            input_key = f"{category_key}_{activity}"
            if f"{input_key}_input" not in st.session_state.emission_values:
                 st.session_state.emission_values[f"{input_key}_input"] = 0.0
            default_value = st.session_state.emission_values.get(f"{input_key}_input", 0.0)
            user_input = st.number_input(label, min_value=0.0, step=0.1, key=input_key, value=float(default_value))
            st.session_state.emission_values[f"{input_key}_input"] = user_input
            try:
                if activity not in df['Activity'].values:
                     st.session_state.emission_values[activity] = 0.0
                     continue
                factor_series = df.loc[df["Activity"] == activity, current_country]
                if not factor_series.empty:
                    factor = factor_series.iloc[0]
                    st.session_state.emission_values[activity] = 0.0 if pd.isna(factor) else user_input * float(factor)
                else:
                    st.session_state.emission_values[activity] = 0.0
            except Exception as e:
                # Keep error reporting minimal unless debugging
                # st.error(f"Calc error for {label}: {e}")
                st.session_state.emission_values[activity] = 0.0

    # Define Activity Lists
    transport_activities = ["Domestic_flight_traveled", "International_flight_traveled", "km_diesel_local_passenger_train_traveled", "km_diesel_long_distance_passenger_train_traveled", "km_electric_passenger_train_traveled", "km_bus_traveled", "km_petrol_car_traveled", "diesel_car_traveled", "km_Motorcycle_traveled", "km_ev_scooter_traveled", "km_ev_car_traveled"]
    food_activities = ["beef_products_consumed", "poultry_products_consumed", "pork_products_consumed", "fish_products_consumed", "other_meat_products_consumed", "dairy_products_consumed", "processed_rice_consumed", "sugar_consumed", "vegetable_oils_fats_consumed", "other_food_products_consumed"]
    energy_water_activities = ["electricity_used", "water_consumed"]
    hotel_activities = ["hotel_stay"]

    # Display Tabs
    current_index = st.session_state.current_tab_index
    if current_index == 0:
        display_activity_inputs(transport_activities, "transport", country)
        if st.button("Next →", key="next_transport", use_container_width=False):
            st.session_state.current_tab_index = 1; st.rerun()
    elif current_index == 1:
        display_activity_inputs(food_activities, "food", country)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Previous", key="prev_food", use_container_width=False):
                st.session_state.current_tab_index = 0; st.rerun()
        with col2:
            if st.button("Next →", key="next_food", use_container_width=False):
                st.session_state.current_tab_index = 2; st.rerun()
    elif current_index == 2:
        display_activity_inputs(energy_water_activities, "energy", country)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Previous", key="prev_energy", use_container_width=False):
                st.session_state.current_tab_index = 1; st.rerun()
        with col2:
            if st.button("Next →", key="next_energy", use_container_width=False):
                st.session_state.current_tab_index = 3; st.rerun()
    elif current_index == 3:
        display_activity_inputs(hotel_activities, "hotel", country)
        if st.button("← Previous", key="prev_hotel", use_container_width=False):
            st.session_state.current_tab_index = 2; st.rerun()

        # Calculation Trigger
        st.divider()
        st.markdown("**Calculate your footprint**")
        reviewed_all = st.checkbox("I have reviewed/entered my data for all categories.", key="review_final_check")
        if reviewed_all:
            if st.button("Calculate My Carbon Footprint", type="primary", use_container_width=True, key="calculate_final_button"):
                emission_values_to_sum = {k: v for k, v in st.session_state.emission_values.items() if not k.endswith('_input') and isinstance(v, (int, float)) and v > 0}
                if not emission_values_to_sum:
                     st.warning("No positive emissions calculated.")
                     st.session_state.calculation_done = False
                else:
                    st.session_state.calculated_emission = sum(emission_values_to_sum.values())
                    def get_avg(name, df_avg):
                        if df_avg is None or "Country" not in df_avg.columns or "PerCapitaCO2" not in df_avg.columns: return None
                        match = df_avg.loc[df_avg["Country"] == name, "PerCapitaCO2"]
                        return match.iloc[0] if not match.empty and pd.notna(match.iloc[0]) else None
                    st.session_state.comparison_plot_data = {
                         "country": {"name": country, "avg": get_avg(country, df1)},
                         "eu": {"name": "EU Average", "avg": get_avg("European Union (27)", df1)},
                         "world": {"name": "World Average", "avg": get_avg("World", df1)}}
                    st.session_state.calculation_done = True
                    st.rerun()
        else:
            st.info("Check the box above to enable calculation.")

    # --- Display Results Area ---
    if st.session_state.get('calculation_done', False):
        st.divider()
        st.subheader("📊 Your Estimated Monthly Carbon Footprint:")
        total_emission = st.session_state.get('calculated_emission', 0)
        if total_emission > 0:
            st.metric(label="kg CO₂ equivalent", value=f"{total_emission:.1f}")
            tree_absorb_monthly = (21.77 / 12.0)
            if tree_absorb_monthly > 0:
                 trees_monthly_equiv = total_emission / tree_absorb_monthly
                 st.markdown(f"Equivalent to CO₂ absorbed by **{trees_monthly_equiv:.1f} trees** in a month.")

            st.divider()
            st.subheader("📈 Comparison with Averages")
            comparison_data = st.session_state.get('comparison_plot_data')
            plot_data_list = []
            captions = []
            world_avg_value = None # Initialize world average value

            # Get World Average for conditional coloring and target line check
            if comparison_data and comparison_data.get('world'):
                world_avg_value = comparison_data['world'].get('avg')

            # --- Conditional Color Logic ---
            you_color = '#1a9850' # Default Green
            color_reason = ""
            if world_avg_value is not None:
                if total_emission > world_avg_value:
                    you_color = '#e41a1c' # Red
                    color_reason = "(above world average)"
                else:
                     color_reason = "(below or equal to world average)"
            color_map = {'You': you_color, 'Average': '#a6cee3'} # Light Blue for Averages
            # --------------------------------

            # Add data to plot list
            plot_data_list.append({"Source": "You", "Emissions": total_emission, "Type": "You"})

            if comparison_data:
                # Iterate and add comparison averages safely
                for key, type_label, default_name in [("country", "Average", country), ("eu", "Average", "EU Average"), ("world", "Average", "World Average")]:
                    data = comparison_data.get(key, {})
                    avg = data.get("avg")
                    name = data.get("name", default_name)
                    if avg is not None:
                         # Don't add 'You' again if it matches country name (edge case)
                         if name != "You":
                            plot_data_list.append({"Source": name, "Emissions": avg, "Type": type_label})
                    else:
                         # Only add caption if the average was expected but missing
                         if key in comparison_data:
                            captions.append(f"Note: Average data for {name} not available.")

            # Display notes about missing data
            for caption in captions:
                st.caption(caption)

            # Plotting section
            if plot_data_list:
                df_comparison = pd.DataFrame(plot_data_list)

                # Define sustainability target
                sustainable_target = 167 # kg CO2e/month (~2 tonnes/year)

                try:
                    fig_comp = px.bar(
                        df_comparison.sort_values("Emissions", ascending=True),
                        x="Emissions", y="Source", orientation='h',
                        color="Type", color_discrete_map=color_map, text="Emissions",
                        # title="Monthly Carbon Footprint Comparison", # Title embedded in subheader now
                        labels={'Emissions': 'kg CO₂ per month', 'Source': '', 'Type': 'Category'}
                    )


                    # Update traces (styling for bars and hover)
                    fig_comp.update_traces(
                         texttemplate='%{text:.1f}', textposition='outside',
                         hovertemplate="<b>%{y}</b><br>Emission: %{x:.1f} kg CO₂<extra></extra>",
                         width=0.5                  
                         )

                    # Update layout (styling for overall chart)
                    fig_comp.update_layout(
                         yaxis={'categoryorder':'total ascending'}, # Order bars by value
                         bargap=0.6, # Adjust gap between bars (controls thickness)
                         height=300,
                         margin=dict(l=5, r=5, t=30, b=20), # Adjust top margin for title space
                         showlegend=False,
                         # title_text="Monthly Carbon Footprint Comparison", # Use layout title
                         # title_x=0.5, # Center title
                         # title_font_size=16
                    )

                    st.plotly_chart(fig_comp, use_container_width=True)

                except Exception as plot_error:
                    st.error(f"Error generating plot: {plot_error}")
                    st.error(traceback.format_exc()) # Show detailed traceback for debugging
            else:
                st.warning("No data available for comparison plot.")
        else:
            st.info("Your calculated emissions are zero. Nothing to display.")


elif not st.session_state.selected_country or st.session_state.selected_country == "-- Select --":
    st.info("Please select your country in Step 1 to begin.")

# --- Sidebar ---
# st.sidebar.markdown("---")
# Add other sidebar elements if needed 
