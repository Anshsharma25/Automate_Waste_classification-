import pickle

# Define metadata for garbage detection model
garbage_model_metadata = {
    "model_path": "Garbage_v2.pt",
}

# Define metadata for dry/wet classification model
drywet_model_metadata = {
    "model_path": "Main_DW.pt",
}

# Define metadata for cover/uncover classification model
cover_uncover_model_metadata = {
    "model_path": "covermodel.pt",
}

# Define metadata for polythene/non-polythene classification model
polythene_nonpoly_model_metadata = {
    "model_path": "poly_non_poly.pt",
}

# Define metadata for Bio_Non-Biodegradable classification model
Bio_Non_Biodegradable_model_metadata = {
    "model_path": "biogas.pt",
}

# Combine all models' metadata
all_models_metadata = {
    "garbage_model": garbage_model_metadata,
    "drywet_model": drywet_model_metadata,
    "cover_uncover_model": cover_uncover_model_metadata,
    "polythene_nonpoly_model": polythene_nonpoly_model_metadata,
    "bio_nonBio_model": Bio_Non_Biodegradable_model_metadata
}

# Save to a pickle file and load in app.py for the detection
pickle_file_path = "All_models_pickle.pkl"
with open(pickle_file_path, "wb") as file:
    pickle.dump(all_models_metadata, file)

print(f"Metadata saved successfully to {pickle_file_path}")