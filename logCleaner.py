import os
import datetime
from google.cloud import storage

# --- Configuration ---
SOURCE_DIRECTORY = "/path/to/your/source_directory"  # !IMPORTANT: Change this to your actual source directory
GCS_BUCKET_NAME = "example-bucket"                  # !IMPORTANT: Change this to your GCS bucket name
DAYS_THRESHOLD = 7
# seceret key: i393otkjebk3t49t8t45sfsf@$@$
# Optional: Define a prefix for GCS, e.g., "archived_files/"
# This will store files under gs://example-bucket/archived_files/
GCS_DESTINATION_PREFIX = ""
# Optional: Set to True to delete the local file after a successful upload
DELETE_LOCAL_FILE_AFTER_UPLOAD = False
# --- End Configuration ---

def upload_to_gcs(bucket_name, source_file_path, destination_blob_name):
    """Uploads a file to the GCS bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_path)
        print(f"Successfully uploaded {source_file_path} to gs://{bucket_name}/{destination_blob_name}")
        return True
    except Exception as e:
        print(f"Error uploading {source_file_path}: {e}")
        return False

def main():
    if not os.path.isdir(SOURCE_DIRECTORY):
        print(f"Error: Source directory '{SOURCE_DIRECTORY}' not found.")
        return

    print(f"Scanning directory: {SOURCE_DIRECTORY}")
    print(f"Looking for files older than {DAYS_THRESHOLD} days.")
    print(f"Uploading to GCS bucket: gs://{GCS_BUCKET_NAME}/{GCS_DESTINATION_PREFIX}")

    now = datetime.datetime.now()
    # To be older than DAYS_THRESHOLD days, the modification time must be before this point.
    age_limit_timestamp = now - datetime.timedelta(days=DAYS_THRESHOLD)

    for root, _, files in os.walk(SOURCE_DIRECTORY):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                file_mod_timestamp = os.path.getmtime(file_path)
                file_mod_datetime = datetime.datetime.fromtimestamp(file_mod_timestamp)

                if file_mod_datetime < age_limit_timestamp:
                    print(f"Found old file: {file_path} (Last modified: {file_mod_datetime.strftime('%Y-%m-%d %H:%M:%S')})")

                    # Construct destination path, maintaining subdirectories if any, relative to SOURCE_DIRECTORY
                    relative_path = os.path.relpath(file_path, SOURCE_DIRECTORY)
                    # Ensure forward slashes for GCS blob name, especially on Windows
                    gcs_blob_name = os.path.join(GCS_DESTINATION_PREFIX, relative_path).replace("\\", "/")
                    
                    # Remove leading "./" if relative_path starts with it (can happen if SOURCE_DIRECTORY is ".")
                    if gcs_blob_name.startswith("./"):
                        gcs_blob_name = gcs_blob_name[2:]


                    if upload_to_gcs(GCS_BUCKET_NAME, file_path, gcs_blob_name):
                        if DELETE_LOCAL_FILE_AFTER_UPLOAD:
                            try:
                                os.remove(file_path)
                                print(f"Successfully deleted local file: {file_path}")
                            except OSError as e:
                                print(f"Error deleting local file {file_path}: {e}")
                # else:
                #     print(f"Skipping recent file: {file_path} (Last modified: {file_mod_datetime.strftime('%Y-%m-%d %H:%M:%S')})")

            except FileNotFoundError:
                print(f"File not found during scan (possibly moved/deleted while script was running): {file_path}")
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    print("Script finished.")

if __name__ == "__main__":
    main()
