import sys
import os
import csv
import scipy.io
from pyproj import Transformer
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# Assuming necessary functions are defined in 'func.py' located in the specified directory
# sys.path.append(r"D:\py_function")
from func import calculate_center_of_geometry

def has_been_processed(file_name, log_file_path):
    try:
        with open(log_file_path, 'r') as log_file:
            processed_files = log_file.read().splitlines()
            return file_name in processed_files
    except FileNotFoundError:
        return False

def log_processed_file(file_name, log_file_path):
    with open(log_file_path, 'a') as log_file:
        log_file.write(file_name + '\n')
        log_file.flush()

def convert_nztm_to_wgs84(easting, northing):
    transformer = Transformer.from_crs("EPSG:2193", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(easting, northing)
    return lon, lat

def get_address_from_coordinates(lon, lat):
    geolocator = Nominatim(user_agent='geoapiTest') # geoapiExercise'
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True)
        if location:
            address = location.raw['address']
            road = address.get('road', 'N/A')
            suburb = address.get('suburb', 'N/A')
            city = address.get('city', 'N/A')
            county = address.get('county', 'N/A')
            state = address.get('state', 'N/A')
            postcode = address.get('postcode', 'N/A')
            return road, suburb, city, county, state, postcode
        else:
            return 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'
    except GeocoderTimedOut:
        return 'Error', 'Error', 'Error', 'Error', 'Error', 'Error'

def read_mat_file(root_directory, cluster_folder, mat_file, writer, csvfile):
    mat_file_path = os.path.join(root_directory, cluster_folder, 'results_TMCMC', mat_file)
    mat_data = scipy.io.loadmat(mat_file_path, variable_names=['X', 'Y'])
    X, Y = mat_data['X'], mat_data['Y']
    X_c, Y_c = calculate_center_of_geometry(X, Y)
    lon_c, lat_c = convert_nztm_to_wgs84(X_c, Y_c)
    road, suburb, city, county, state, postcode = get_address_from_coordinates(lon_c, lat_c)

    result = {
        "Cluster": cluster_folder,
        "mat_file_name": mat_file,
        "X_c": X_c,
        "Y_c": Y_c,
        "lon_c": lon_c,
        "lat_c": lat_c,
        "road": road,
        "suburb": suburb,
        "city": city,
        "county": county,
        "state": state,
        "postcode": postcode
    }
    writer.writerow(result)
    csvfile.flush()

def process_file(file_name, root_directory, cluster_folder, writer, log_file_path, csvfile):
    if not has_been_processed(file_name, log_file_path):
        read_mat_file(root_directory, cluster_folder, file_name, writer, csvfile)
        print(f"Processed file: {file_name}")
        log_processed_file(file_name, log_file_path)
    else:
        print(f"Skipped already processed file: {file_name}")

def process_cluster(root_directory, cluster_folder, writer, log_file_path, csvfile):
    print(f"Processing Cluster: {cluster_folder}...")
    cluster_path = os.path.join(root_directory, cluster_folder)
    if os.path.isdir(cluster_path) and cluster_folder.startswith('Cluster '):
        tmcmc_folder = os.path.join(cluster_path, 'results_TMCMC')
        if os.path.exists(tmcmc_folder) and os.path.isdir(tmcmc_folder):
            for mat_file in os.listdir(tmcmc_folder):
                if mat_file.endswith('.mat'):
                    process_file(mat_file, root_directory, cluster_folder, writer, log_file_path, csvfile)
    print(f"Finished processing Cluster: {cluster_folder}")

if __name__ == "__main__":
    log_file_path = 'processed_files.log'
    root_directory = r"../"  # Adjust as necessary

    with open('results.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Cluster', 'mat_file_name', 'X_c', 'Y_c', 'lon_c', 'lat_c', 'road', 'suburb', 'city', 'county', 'state', 'postcode']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        csvfile.flush()  # Flush after writing the header

        for item in os.listdir(root_directory):
            if os.path.isdir(os.path.join(root_directory, item)):  # Ensure it's a directory
                process_cluster(root_directory, item, writer, log_file_path, csvfile)
