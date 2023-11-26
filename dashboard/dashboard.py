import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards 
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import seaborn as sns
from babel.numbers import format_currency
sns.set(style='dark')

def create_daily_orders_df(df):
    daily_orders_df = df[df['order_status'] =='delivered'].resample(rule='D', on='order_purchase_timestamp').agg({
        'order_id': 'nunique',
        'payment_value': 'sum'
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        'order_id': 'order_count',
        'payment_value': 'transaction'
    }, inplace=True)
    
    return daily_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = df[df['order_status'] =='delivered'].groupby('product_category_name_english').product_id.count().sort_values(ascending=False).reset_index()
    sum_order_items_df = sum_order_items_df.rename(columns={
        'product_id' : 'quantity'
    })
    return sum_order_items_df

def create_order_bystate_df(df):
    bystate_df = df[df['order_status'] =='delivered'].groupby(by='customer_state').order_id.nunique().reset_index()
    bystate_df.rename(columns = {
    'order_id' : 'order_count',
    },inplace=True)
    return bystate_df


def create_order_bycity_df(df):
    delivered_df = df[df['order_status'] == 'delivered']
    bycity_df = delivered_df.groupby(by='customer_city').agg({
        'order_id': 'nunique',
        'customer_zip_code_prefix': 'nunique'
    }).reset_index()
    bycity_df.rename(columns={
        'order_id': 'order_count',
    }, inplace=True)
    geolocation_df = pd.read_csv('./data/geolocation_dataset.csv')
    geolocation_mode = geolocation_df.groupby('geolocation_city').agg({
        'geolocation_lat': lambda x: x.mode().iloc[0],
        'geolocation_lng': lambda x: x.mode().iloc[0]
    }).reset_index()
    new_bystate_df = pd.merge(
        left=bycity_df,
        right=geolocation_mode[['geolocation_city', 'geolocation_lat', 'geolocation_lng']],
        how='left',
        left_on=['customer_city'],
        right_on=['geolocation_city']
    )
    new_bystate_df.drop(columns=['geolocation_city'], inplace=True)

    return new_bystate_df

def create_sum_order_canceled_df(df):
    sum_order_canceled = df[df['order_status'] == 'canceled'].resample(rule='D', on='order_purchase_timestamp').agg({
        'order_id' : 'nunique',
        'payment_value' : 'sum'
  })
    sum_order_canceled = sum_order_canceled.reset_index()
    sum_order_canceled.rename(columns={
        'order_id': 'order_count',
        'payment_value': 'transaction'
    }, inplace=True)
    return sum_order_canceled

def create_sum_order_payment_method_df(df):
    sum_order_payment_method_df= df.groupby('payment_type').order_id.nunique().reset_index()
    sum_order_payment_method_df.rename(columns = {
        'order_id' : 'order_count'
        },inplace=True)
    return sum_order_payment_method_df

def create_count_customer_by_state_df(df):
    count_customer_by_state_df = df.groupby(by='customer_state').customer_id.nunique().reset_index()
    count_customer_by_state_df.rename(columns = {
        'customer_id' : 'customer_count'
        },inplace=True)
    return count_customer_by_state_df

def create_count_customer_by_city_df(df):
    count_customer_by_city_df = df.groupby(by='customer_city').customer_id.nunique().reset_index()
    count_customer_by_city_df.rename(columns = {
        'customer_id' : 'customer_count'
        },inplace=True)
    return count_customer_by_city_df

def create_rfm_df(df):
    orders_df = pd.read_csv('./data/orders_dataset.csv')
    datetimes_orders_df = ['order_purchase_timestamp','order_approved_at','order_delivered_carrier_date','order_delivered_customer_date','order_estimated_delivery_date']
    for column in datetimes_orders_df:
        orders_df[column]= pd.to_datetime(orders_df[column])
    rfm_df = all_df.groupby(by='customer_id', as_index=False).agg({
        'order_purchase_timestamp': 'max',
        'order_id': 'nunique',
        'payment_value': 'sum' 
    })
    rfm_df.columns = ['customer_id', 'max_order_timestamp', 'frequency', 'monetary']
    rfm_df['max_order_timestamp'] = rfm_df['max_order_timestamp'].dt.date
    recent_date = orders_df['order_purchase_timestamp'].dt.date.max()
    rfm_df['recency'] = rfm_df['max_order_timestamp'].apply(lambda x: (recent_date - x).days)
    rfm_df.drop('max_order_timestamp', axis=1, inplace=True)
    
    return rfm_df

custom_css = '''
            <style>
                .st-emotion-cache-1y4p8pa {
                    width: 100%;
                    padding: 6rem 1rem 10rem;
                    max-width: 75rem;
                }
            </stlye>
                '''
st.markdown(custom_css, unsafe_allow_html=True)
all_df = pd.read_csv('./dashboard/all_data.csv')

datetime_columns = ['order_purchase_timestamp']
all_df.sort_values(by='order_purchase_timestamp', inplace=True)
all_df.reset_index(inplace=True)
 
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

min_date = all_df['order_purchase_timestamp'].min()
max_date = all_df['order_purchase_timestamp'].max()

with st.sidebar:
    st.image('./images/logo.png',width=200)
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
if start_date is not None and end_date is not None:
    st.success(f"Rentang Data: {start_date} hingga {end_date}")
else:
    st.warning("Silahkan input rentang tanggal.")

main_df = all_df[(all_df['order_purchase_timestamp'] >= str(start_date)) & 
                (all_df['order_purchase_timestamp'] <= str(end_date))]

daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bystate_df = create_order_bystate_df(main_df)
bycity_df = create_order_bycity_df(main_df)
order_canceled = create_sum_order_canceled_df(main_df)
sum_order_payment_method_df = create_sum_order_payment_method_df(main_df)
count_customer_by_state_df = create_count_customer_by_state_df(main_df)
count_customer_by_city_df = create_count_customer_by_city_df(main_df)
rfm_df = create_rfm_df(main_df)

st.header('Olist E-Commerce Data Dashboard:sparkles:',divider='blue')

st.subheader('➡️ Daily Orders')

col1, col2,col3 = st.columns(3) 
with col1:
    total_orders = daily_orders_df.order_count.sum()
    col1.metric(label='Total Delivered Orders', value=total_orders, delta=None)
    style_metric_cards()

with col2:
    total_canceled_orders = order_canceled.order_count.sum()
    col2.metric(label='Total Canceled Orders', value=total_canceled_orders, delta=None)
    style_metric_cards()

with col3:
    total_transaction = format_currency(daily_orders_df.transaction.sum(), 'BRL ', locale='pt_BR')
    col3.metric(label='Total transaction', value=total_transaction, delta=None)
    style_metric_cards()
with st.expander('Data Preview'):
    main_df_sorted = main_df.sort_values(by='order_purchase_timestamp')
    st.dataframe(
        main_df_sorted,
    ) 


fig, ax = plt.subplots(figsize=(16, 8))


col1, col2= st.columns(2)
with col1:
    fig_order_count = px.line(
        daily_orders_df,
        x='order_purchase_timestamp',
        y='order_count',
        markers=False,
    )
    fig_order_canceled =  px.line(
        order_canceled,
        x='order_purchase_timestamp',
        y='order_count',
        markers=False,
    )
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=['Order Delivery Count', 'Order Canceled Count'])
    fig.add_trace(fig_order_count['data'][0],row=1, col=1)
    fig.add_trace(fig_order_canceled['data'][0], row=2, col=1)
    fig.update_layout(width=500, title_text='Order Count and Order Canceled Over Time')
    st.plotly_chart(fig)
with col2:
    fig_total_transaction = px.line(
        daily_orders_df,
        x='order_purchase_timestamp',
        y='transaction',
        title='Total Transactions',
        width=500
    )
    fig_total_transaction.update_xaxes(title_text=None)
    st.plotly_chart(fig_total_transaction)


st.subheader('➡️ Highest Order Distributions')
col11,col2 = st.columns(2)
with col11:
    fig_order_by_state = px.bar(
        bystate_df.sort_values(by='order_count',ascending=False).head(), 
                                x='customer_state', 
                                y='order_count',
                                width=500,
                                title='Order Quantity by State')
    st.plotly_chart(fig_order_by_state)

with col2:
    fig_order_by_city = px.bar(
    bycity_df.sort_values(by='order_count',ascending=False).head(), 
                            x='customer_city', 
                            y='order_count',
                            width=500,
                            title='Order Quantity by City')
    st.plotly_chart(fig_order_by_city)

col1,col2 = st.columns(2)
with col1:
    fig_map = px.scatter_mapbox(
    bycity_df.sort_values(by='order_count',ascending=False).head(200),
    lat='geolocation_lat',
    lon='geolocation_lng',
    color='order_count',
    size='order_count',
    title= 'Geoanalysis', 
    width=600,
    hover_name='customer_city',
    hover_data=['order_count'],
    mapbox_style='carto-positron',  
    zoom=3,
    color_continuous_scale=px.colors.sequential.Viridis
    )
    st.plotly_chart(fig_map)
with col2:
    fig_pie= px.pie(sum_order_payment_method_df, 
                    values='order_count', 
                    names='payment_type',
                    width=500,
                    title= 'Comparison of Customer Payment Method Usage', 
                    hole=0.4,
                    color='payment_type',
                    color_discrete_map={'credit_card':'lightcyan',
                                        'boleto':'cyan',
                                        'voucher':'royalblue',
                                        'debit_card':'darkblue'})
    st.plotly_chart(fig_pie)

st.subheader('➡️ Best & Worst Performing Product')
col1, col2 = st.columns(2)
with col1 :
    fig_best_performing = px.bar(
        sum_order_items_df.sort_values(by='quantity', ascending=False).head(5),
        x='quantity',
        y='product_category_name_english',
        orientation='h',
        width=500,
        color_discrete_sequence=['#0125d0']
    )
    fig_best_performing.update_layout(
        xaxis_title='Number of Sales',
        yaxis_title=None,
        title='Best Performing Product',
        title_font_size=25,
        yaxis=dict(tickfont=dict(size=15)),
        xaxis=dict(tickfont=dict(size=15))
    )
    st.plotly_chart(fig_best_performing)

with col2 :
    fig_worst_performing = px.bar(
        sum_order_items_df.sort_values(by='quantity', ascending=True).head(5),
        x='quantity',
        y='product_category_name_english',
        orientation='h',
        width=500,
        color_discrete_sequence=['#0125d0']
    )
    fig_worst_performing.update_layout(
        xaxis_title='Number of Sales',
        yaxis_title=None,
        title='Worst Performing Product',
        title_font_size=25,
        yaxis=dict(tickfont=dict(size=15)),
        xaxis=dict(tickfont=dict(size=15)),
        xaxis_autorange='reversed'
    )
    st.plotly_chart(fig_worst_performing)

st.subheader('➡️ most buyers')
col1,col2 = st.columns(2)
with col1:
    fig_customer_by_state_df = px.bar(
        count_customer_by_state_df.sort_values(by='customer_count',ascending=False).head(),
        x='customer_count',
        y='customer_state',
        title= 'highest distribution of customers by state',
        orientation='h',
        width=500,
        color_discrete_sequence=['#0125d0']
        )
    st.plotly_chart(fig_customer_by_state_df)

with col2:
    fig_customer_by_city_df = px.bar(
        count_customer_by_city_df.sort_values(by='customer_count',ascending=False).head(),
        x='customer_count',
        y='customer_city',
        title = 'highest distribution of customers by city',
        orientation='h',
        width=500,
        color_discrete_sequence=['#0125d0']
        )
    st.plotly_chart(fig_customer_by_city_df)

st.subheader('➡️ Best Customer Based On RFM Parameters')
col1, col2, col3 = st.columns(3)

with col1 :
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric('Average recency (days)', value=avg_recency)

with col2 :
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric('Average Frequency', value=avg_frequency)

with col3 :
    avg_monetary = format_currency(rfm_df.monetary.mean(),'BRL ', locale='pt_BR')
    st.metric('Average Monetary', value=avg_monetary)

fig_recency = px.bar(
    rfm_df.sort_values(by='recency', ascending=True).head(5),
    y='customer_id',
    x='recency',
    title='By Recency (days)',
    labels={'recency': 'Recency (days)'},
    color_discrete_sequence=['#90CAF9'] * 5
)
fig_recency.update_xaxes(title_text='customer_id', tickfont_size=20)
fig_recency.update_yaxes(title_text='Recency (days)', tickfont_size=20)
fig_recency.update_layout(font=dict(size=30))
st.plotly_chart(fig_recency)


fig_frequency = px.bar(
    rfm_df.sort_values(by='frequency', ascending=False).head(5),
    y='customer_id',
    x='frequency',
    title='By Frequency',
    labels={'frequency': 'Frequency'},
    color_discrete_sequence=['#90CAF9'] * 5
)
fig_frequency.update_xaxes(title_text='customer_id', tickfont_size=20)
fig_frequency.update_yaxes(title_text='Frequency', tickfont_size=20)
fig_frequency.update_layout(font=dict(size=30))
st.plotly_chart(fig_frequency)


fig_monetary = px.bar(
    rfm_df.sort_values(by='monetary', ascending=False).head(5),
    y='customer_id',
    x='monetary',
    title='By Monetary',
    labels={'monetary': 'Monetary'},
    color_discrete_sequence=['#90CAF9'] * 5
)
fig_monetary.update_xaxes(title_text='customer_id', tickfont_size=20)
fig_monetary.update_yaxes(title_text='Monetary', tickfont_size=20)
fig_monetary.update_layout(font=dict(size=30))
st.plotly_chart(fig_monetary)

st.caption('Copyright (c) Candra Burhanudin 2023')
