# Import python packages.
import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, when_matched

# Create a Snowpark session manually
@st.cache_resource
def create_session():
    return Session.builder.configs({
        "account": st.secrets["account"],
        "user": st.secrets["user"],
        "password": st.secrets["password"],
        "role": st.secrets["role"],
        "warehouse": st.secrets["warehouse"],
        "database": st.secrets["database"],
        "schema": st.secrets["schema"],
    }).create()

session = create_session()

# --- TEST SNOWFLAKE CONNECTION ---
try:
    info = session.sql("SELECT CURRENT_USER(), CURRENT_ROLE()").collect()
    st.success(f"Connected as {info[0][0]} using role {info[0][1]}")
except Exception as e:
    st.error(f"Connection failed: {e}")

# Write directly to the app.
st.title(":cup_with_straw: Pending Smoothie Orders :cup_with_straw:")
st.write("Orders that need to be filled.")

# Query pending orders
my_dataframe = (
    session.table("smoothies.public.orders")
    .filter(col("ORDER_FILLED") == 0)
    .collect()
)

if my_dataframe:
    editable_df = st.data_editor(my_dataframe)
    submitted = st.button("Submit")

    if submitted:
        og_dataset = session.table("smoothies.public.orders")
        edited_dataset = session.create_dataframe(editable_df)

        try:
            og_dataset.merge(
                edited_dataset,
                og_dataset["ORDER_UID"] == edited_dataset["ORDER_UID"],
                [
                    when_matched().update({
                        "ORDER_FILLED": edited_dataset["ORDER_FILLED"]
                    })
                ]
            )
            st.success("Orders updated successfully", icon="👍")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

else:
    st.success("There are no pending orders right now", icon="👍")
