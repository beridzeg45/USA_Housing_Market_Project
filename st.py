import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import pickle
import requests
import json
import warnings
warnings.filterwarnings('ignore')
import sqlite3
import datetime


grouped_zip=pd.read_csv('grouped_zip.csv')
grouped_city=pd.read_csv('grouped_city.csv')
states_shp_urls_dict=pickle.load(open('states_shp_urls_dict.pickle','rb'))


grouped_zip['RegionName']=grouped_zip['RegionName'].astype(str)
last_period=str(grouped_city['Date'].max())

all_cities=list(grouped_city['City_State'].unique())


def return_scatter_mapbox():
    filtered=grouped_city[grouped_city['Date']==last_period]

    fig=px.scatter_mapbox(filtered,lon='Lon',lat='Lat',zoom=3.5,
                        color='Price', color_continuous_scale='Plotly3',
                        size='Price',
                        hover_name='City_State')
    fig.update_layout(mapbox_style='open-street-map')
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0),template='plotly_dark',height=600,width=2000)
    fig.update_layout(title=dict(text='Biggest USA Cities And AVerage House Prices',font_family='Arial Black'))
    fig.update_layout(coloraxis_showscale=False)
    scatter_mapbox_fig=fig
    return scatter_mapbox_fig


def return_price_fig(input_values_list):
    filtered=grouped_city[grouped_city['City_State'].isin(input_values_list)]
    filtered['Change']=filtered.groupby('City_State')['Price'].transform(lambda x:x)/filtered.groupby('City_State')['Price'].transform(lambda x:x.shift(1))-1

    fig=px.scatter(filtered,x=filtered['Date'].astype(str),y='Price',color='City_State',hover_name=filtered['Date'].astype(str))
    fig.update_layout(template='plotly_dark')
    fig.update_layout(title=dict(text='House Prices Over Time By City',font_family='Arial Black'))
    fig.update_xaxes(title_text=None)
    fig.update_yaxes(tickformat='$,.0f',title_text='Price')
    price_fig=fig
    return price_fig


def return_change_fig(input_values_list):
    filtered=grouped_city[grouped_city['City_State'].isin(input_values_list)]
    filtered['Change']=filtered.groupby('City_State')['Price'].transform(lambda x:x)/filtered.groupby('City_State')['Price'].transform(lambda x:x.shift(1))-1

    if len(input_values_list)>1:
        fig=px.scatter(filtered,x=filtered['Date'].astype(str),y='Change',color='City_State',hover_name=filtered['Date'].astype(str))
        fig.update_traces(mode='markers+lines',line_width=1,marker_size=4)
    else:
        fig=px.bar(filtered,x=filtered['Date'].astype(str),y='Change',color='City_State',hover_name=filtered['Date'].astype(str))

    fig.update_layout(template='plotly_dark')
    fig.update_layout(title=dict(text='Change In House Prices Over Time By City',font_family='Arial Black'))
    fig.update_xaxes(title_text=None)
    fig.update_yaxes(tickformat='.1%',title_text='Price')
    change_fig=fig
    return change_fig


def return_choropleth_fig(input_value):
    filtered=grouped_zip[grouped_zip['City_State']==input_value]
    city_state=filtered['City_State'].unique()[0]
    state=city_state.split('(')[-1].split(')')[0]
    unique_zipcodes=list(filtered['RegionName'].unique())


    response=requests.get(states_shp_urls_dict[state])
    data = response.json()
    filtered_zipcodes=[entry for entry in data["features"] if entry["properties"]["ZCTA5CE10"] in unique_zipcodes]
    gdf=geopandas.GeoDataFrame.from_features(filtered_zipcodes)

    filtered=filtered.merge(gdf[['ZCTA5CE10','geometry']],how='left',left_on='RegionName',right_on='ZCTA5CE10')
    filtered=filtered.sort_values('Price',ascending=False).reset_index(drop=True)
    filtered=geopandas.GeoDataFrame(filtered,geometry='geometry')
    try:
        fig = px.choropleth_mapbox(filtered,
                            geojson=filtered.geometry,
                            locations=filtered.index,
                            color='Price',opacity=1,color_continuous_scale='Plotly3',
                            hover_name='RegionName'
                            )
        fig.update_layout(mapbox_style='carto-positron',mapbox_center={'lat': filtered.geometry.centroid.y.mean(), 'lon': filtered.geometry.centroid.x.mean()},mapbox_zoom=9)
        fig.update_layout(height=1000,width=1000,margin=dict(l=0,r=0,t=30,b=0),template='plotly_dark')
        fig.update_layout(title=dict(text=f'House Prices Heatmap Based On ZipCodes In {city_state}',font_family='Arial Black'))
        fig.update_layout(coloraxis_showscale=False)
        fig.update_traces(marker_line_width=0.1)
        choropleth_fig=fig
    except:
        choropleth_fig=None
    return choropleth_fig




#streamlit
st.set_page_config(layout='wide')
st.header('USA Housing Market Overview 🏠📈📉- Python Project By Giorgi Beridze')

scatter_mapbox_fig = return_scatter_mapbox()
st.plotly_chart(scatter_mapbox_fig, use_container_width=True)


input_values_list=st.multiselect(label='',placeholder='Type city name (or multiple names for comparison)',options=['']+all_cities)
if st.button('Show Prices By City') and input_values_list:
    col1,col2=st.columns(2)
    price_fig=return_price_fig(input_values_list)
    change_fig=return_change_fig(input_values_list)

    with col1:
        st.plotly_chart(price_fig,use_container_width=True)
    with col2:
        st.plotly_chart(change_fig,use_container_width=True)


input_value=st.selectbox(label='',placeholder='Type city name (this may take 10-15 seconds)',options=['']+all_cities)
if st.button('Show Prices By Zip Code') and input_value:
    with st.spinner('Estimated time to the graph is 10-15 seconds...'):
        choropleth_fig=return_choropleth_fig(input_value)
        st.plotly_chart(choropleth_fig, use_container_width=True)


#sqlite3
connection = sqlite3.connect('database.db')
cursor = connection.cursor()

def insert_data_into_db():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO visits (Timestamp) VALUES (?)", (timestamp,))
    connection.commit()

def get_visits_by_date():
    total_visits = cursor.execute('SELECT COUNT(VisitID) FROM visits').fetchone()[0]
    visits_by_date_df=pd.read_sql("SELECT DATE(Timestamp) as visit_date, COUNT(VisitID) as VisitsCount FROM visits GROUP BY DATE(Timestamp)",connection)
    visits_by_date_df.columns=['Date','Visits Count']
    return total_visits, visits_by_date_df

def create_visits_graph():
    total_visits, visits_by_date_df=get_visits_by_date()
    
    fig,ax=plt.subplots()
    visits_by_date_df.plot(ax=ax,x='Date',y='Visits Count',marker='o')
    ax.set_title('Number Of Wbsite Visitors By Date',fontweight='bold')
    ax.set_xlabel(None)
    return fig
    
insert_data_into_db()
    


# Add intro text to upper left corner
st.sidebar.markdown("# About me:")

intro_text = """
Hi!👋 \n
I'm Giorgi, and this is my another python project : USA House Prices Analysis.\n
It involves following python librarries in action: pandas, plotly, sqlite3.\n
If you're curious about the code and want to explore it, feel free to visit my [Github account!](https://github.com/beridzeg45)\n
"""
total_visits, visits_by_date_df=get_visits_by_date()
fig=create_visits_graph()

st.sidebar.markdown(intro_text)
st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
st.sidebar.markdown(f'<p style="font-size:20px;">Total Website Visits: {total_visits}</p>', unsafe_allow_html=True)
st.sidebar.pyplot(fig)

with open("database.db", "rb") as file:
    st.sidebar.download_button(
        label="Download Database",
        data=file,
        file_name="database.db",
        mime="application/octet-stream"
    )
    
#close sqlite3 connection
connection.close()


