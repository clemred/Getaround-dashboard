import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


### ----------------------------------------------------
### INTRODUCTION TEXT
### ----------------------------------------------------


st.write('# Getaround dashboard \n ---')
st.write('When using Getaround, drivers book cars for a specific time period, from an hour to a few days long. They are supposed to bring back the car on time, but it happens from time to time that drivers are late for the checkout.')
st.write('In order to mitigate those issues we have decided to implement a minimum delay between two rentals.')
st.write('Here are some charts to decide the threshold (how long should the minimum delay be?) and the scope (should we enable the feature for all cars?)')
st.write('---')


### ----------------------------------------------------
### FILE READING AND FILTERING
### ----------------------------------------------------


df_raw = pd.read_excel("../data/get_around_delay_analysis.xlsx")

df = df_raw
df = df.drop('car_id', axis=1)
previous_list = list(df[df.previous_ended_rental_id.notna()].previous_ended_rental_id)
df_previous = df[df.rental_id.isin(previous_list)]
df = df.merge(df_previous, left_on='previous_ended_rental_id', right_on='rental_id', how='left')
df = df.drop(['rental_id_x', 'previous_ended_rental_id_x', 'rental_id_y', 'previous_ended_rental_id_y', 'time_delta_with_previous_rental_in_minutes_y'], axis=1)
df = df.rename(columns={'checkin_type_x': 'check_type',
                                    'state_x': 'state',
                                    'delay_at_checkout_in_minutes_x': 'delay_at_checkout_in_minutes',
                                    'time_delta_with_previous_rental_in_minutes_x': 'time_delta_with_previous_rental_in_minutes',
                                    'checkin_type_y': 'p_check_type',
                                    'state_y': 'p_state',
                                    'delay_at_checkout_in_minutes_y': 'p_delay_at_checkout_in_minutes'})

# Turning every dealy in hours
df['checkout_delay_hours'] = df['delay_at_checkout_in_minutes'] / 60
df['p_checkout_delay_hours'] = df['p_delay_at_checkout_in_minutes'] / 60
df['time_delta_with_previous_rental'] = df['time_delta_with_previous_rental_in_minutes'] / 60
df = df.drop(['delay_at_checkout_in_minutes', 'p_delay_at_checkout_in_minutes', 'time_delta_with_previous_rental_in_minutes'], axis=1)

# Creating labels "late", "on time" and "early"
df['checkout_delay'] = df.checkout_delay_hours.map(
    lambda x: 'late' if x > 0 else('early' if x < 0 else 'on time'))
df['p_checkout_delay'] = df.p_checkout_delay_hours.map(
    lambda x: 'late' if x > 0 else('early' if x < 0 else 'on time'))


### ----------------------------------------------------
### Data insights
### ----------------------------------------------------


### ----------------------------------------------------
### Data insights - How often are drivers late for the next check-in?
### ----------------------------------------------------


st.write('## How often are drivers late for the next check-in?')
st.write('We will only consider ended previous rentals for this question. If their checkout delay is longer than time delta with the next rental, then they count.')

n_ended_previous_rentals = df[df.p_state.notna()].shape[0]
n_next_checkin_late = df[df.p_checkout_delay_hours > df.time_delta_with_previous_rental].shape[0]

st.write(f'There is a total of {n_ended_previous_rentals} ended previous rentals and {n_next_checkin_late} drivers that were late for the next checkin.')
st.write(f'So, when there is a next checkin, drivers are late {n_next_checkin_late/n_ended_previous_rentals:.2%} of the time')
st.write('---')



### ----------------------------------------------------
### Data insights - How does it impact the next driver?
### ----------------------------------------------------


st.write('## How does it impact the next driver? ')

fig = px.pie(df[df.p_checkout_delay_hours > df.time_delta_with_previous_rental],
            'state',
            title='Rental canceled probably because previous driver was late',
            width=800)
st.plotly_chart(fig)
st.write('---')


### ----------------------------------------------------
### Data insights - Scope
### ----------------------------------------------------


st.write('## Scope')
st.write('Scope correspond to the two choices clients have for the checkin and checkout flow:')
st.write('**Mobile** rental agreement on native apps: driver and owner meet and both sign the rental agreement on the owner’s smartphone')
st.write('**Connect**: the driver doesn’t meet the owner and opens the car with his smartphone')
st.write('Select the scope for the next questions with the drop down menu below:')

check_type = st.selectbox("Select scope:", ['Full scope'] + list(df['check_type'].dropna().unique()))
st.write('---')


### ----------------------------------------------------
### Data insights - How many rentals would be affected by the feature depending on the threshold and scope we choose? 
### ----------------------------------------------------


st.write('## How many rentals would be affected by the feature depending on the threshold and scope we choose?')

# Filter data
sub_df = df if check_type == 'Full scope' else df[df['check_type'] == check_type]

# Threshold slider
threshold = st.slider("Selected threshold (hours):", min_value=0., max_value=12., value=0.0, step=0.5)

# Calculate counts
inf = int((sub_df['time_delta_with_previous_rental'] < threshold).sum())
sup = len(sub_df) - inf

# Render Plotly chart
fig = go.Figure(
    data=[
        go.Pie(
            labels=['Affected', 'Not affected'],
            values=[inf, sup],
            sort=False,
        )
    ]
)

fig.update_layout(title="Rentals affected by the new feature")
st.plotly_chart(fig)
st.write('---')


### ----------------------------------------------------
### Data insights - How many problematic cases will it solve depending on the chosen threshold and scope?
### ----------------------------------------------------


st.write('## How many problematic cases will it solve depending on the chosen threshold and scope?')
st.write('For this question we will only consider rentals for which the driver was late for the next checkin.')

# Filter data
df = df[df.p_checkout_delay_hours > df.time_delta_with_previous_rental]
sub_df = df if check_type == 'Full scope' else df[df['check_type'] == check_type]

# Threshold slider
threshold = st.slider("Selected threshold (hours):", min_value=0., max_value=20., value=0.0, step=0.5)

# Calculate counts
inf = int((sub_df['p_checkout_delay_hours'] < threshold).sum())
sup = len(sub_df) - inf

# Render Plotly chart
fig = go.Figure(
    data=[
        go.Pie(
            labels=['Would be solved', "Wouldn't be solved"],
            values=[inf, sup],
            sort=False,
        )
    ]
)

fig.update_layout(title="Problematic cases that  would be solved by the new feature")
st.plotly_chart(fig)
st.write('---')