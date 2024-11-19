# assumeing the script is executed on the server where the disk space needs to be monitored.

import psutil
import os
from datetime import datetime, timedelta

def check_disk_usage(path="/"):
    usage = psutil.disk_usage(path)
    print(f"Disk Usage for {path}: {usage.percent}% used")
    return usage.percent

def find_old_files(directory, days_old=30):
    cutoff_date = datetime.now() - timedelta(days=days_old)
    old_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_modified_date = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if file_modified_date < cutoff_date:
                old_files.append(file_path)

    return old_files

def delete_files(file_list):
    for file_path in file_list:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def main():
    # Set the threshold for alerts
    THRESHOLD = 80  # in percentage

    # Step 1: Monitor Disk Usage
    # The root directory (/) includes only the system's critical read-only files, whereas the Data volume (/System/Volumes/Data) contains the actual user and app data.

    if check_disk_usage("/System/Volumes/Data") > THRESHOLD:
        print("Warning: Disk usage is high!")
        
        # Step 2: Identify Old Files
        old_files = find_old_files("/var/log", days_old=30)
        
        if old_files:
            print(f"Files to delete: {old_files}")
            # Step 3: Delete Old Files
            # delete_files(old_files)
        else:
            print("No old files found to delete.")
    else:
        print("Disk usage is within acceptable limits.")
    
    # Step 4: Predictive Analysis (Optional)
    # Train and predict disk usage trends
    future_usage = model.predict(np.array([[6], [7], [8]]))
    print(f"Predicted disk usage for future days: {future_usage}")

if __name__ == "__main__":
    main()

