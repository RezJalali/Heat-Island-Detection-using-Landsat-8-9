import ee
import geemap
import pandas as pd

try:
    ee.Initialize('github-projects-464906')
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

# Define the Area of Interest (AOI) for Isfahan
ROI = ee.Geometry.Rectangle([51.5, 32.5, 52.0, 32.8])

# Create an interactive map centered on Isfahan
vis_map = geemap.Map(center=[32.65, 51.66], zoom=11)
vis_map.addLayer(ROI, {}, 'Isfahan AOI')

# Define Start and End dates
start_date = '2024-01-01'
end_date = '2024-12-30'
# Generate a list of dates for each month in 2024
dates = pd.date_range(start=start_date, end=end_date, freq='MS')

# A list to store our monthly procucts
monthly_products = []

# A function to load landsat 8 and 9 images and mask cloudy images
def landsat_image_collection (ROI,start_month, end_month):
    landsat_collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .merge((ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))) \
        .filterBounds(ROI) \
        .filterDate(start_month, end_month) \
        .filter(ee.Filter.lt('CLOUD_COVER', 10)) # Filtering images with less than 10% cloud cover
    return landsat_collection
# A function to retrieve surface temperature data in celsius
def process_image (image):
    surface_temp = image.select('ST_B10')
    # apply the specified scale factor and convert Kelvin to Celsius
    celsius_st = surface_temp.multiply(0.00341802).add(149.0).subtract(273.15)
    return celsius_st.rename('LST').copyProperties(image, ['system:time_start'])

# Looping through each month to calculate indices
for date in dates:
    start_month = date.strftime('%Y-%m-%d')
    end_month = (date + pd.DateOffset(months=1)).strftime('%Y-%m-%d')
    month_name = date.strftime('%B %Y')
    # Retrieving Landsat 8 & 9 images for the ROI and the specified duration
    img_coll = landsat_image_collection(ROI,start_month,end_month)
    lst_product = img_coll.map(process_image)
    monthly_lst = lst_product.max().clip(ROI).set('month_name',month_name)
    monthly_products.append(monthly_lst)

# Create an Image Collection from the monthly land surface temperature products
lst_collection = ee.ImageCollection.fromImages(monthly_products)
print(f"\nThere are {lst_collection.size().getInfo()} images in the collection")

# Define visualization parameters for the Land Surface Temperature
lst_vis_params = {
    'min': 0, 'max': 70,  # Temperature range in Celsius
    'palette': [
        '000080', '0000D9', '4000FF', '8000FF', '0080FF', '00FFFF',
        '00FF80', '80FF00', 'FFFF00', 'FF8000', 'FF0000', '800000'
    ]
}

# Add the entire collection to the map as one layer
vis_map.addLayer(lst_collection, lst_vis_params, 'Monthly LST')
# Add a color bar legend and a layer control to the map.
vis_map.add_colorbar(lst_vis_params, label="Max Monthly NDVI")
vis_map.add_layer_control()
# add a slider to move between the months
vis_map.add_time_slider(lst_collection, vis_params=lst_vis_params, time_interval=2, labels=lst_collection.aggregate_array('month_name').getInfo())
