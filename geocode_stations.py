import pandas as pd

print("Loading data files...")
fuel_df = pd.read_csv("fuel-prices-for-be-assessment.csv")
cities_df = pd.read_csv("uscities.csv")

fuel_df["city_clean"] = fuel_df["City"].astype(str).str.strip().str.lower()
fuel_df["state_clean"] = fuel_df["State"].astype(str).str.strip().str.upper()

cities_df["city_clean"] = cities_df["city"].astype(str).str.strip().str.lower()
cities_df["state_clean"] = cities_df["state_id"].astype(str).str.strip().str.upper()

merged = fuel_df.merge(
    cities_df[["city_clean", "state_clean", "lat", "lng"]],
    on=["city_clean", "state_clean"],
    how="inner"
).rename(columns={"lat": "latitude", "lng": "longitude"})

merged = merged.drop(columns=["city_clean", "state_clean"]).dropna(subset=["latitude", "longitude"])

output_file = "fuel_prices_with_coordinates.csv"
merged.to_csv(output_file, index=False)

print(f"Done! {len(merged)} stations geocoded and saved to {output_file}.")
