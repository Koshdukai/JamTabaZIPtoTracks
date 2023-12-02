from pydub import AudioSegment
import os
import zipfile
import json
import sys
import glob

# Set the path to ffmpeg and ffprobe executables if needed
# pydub.AudioSegment.ffmpeg = "/path/to/ffmpeg"
# pydub.AudioSegment.ffprobe = "/path/to/ffprobe"

def generate_tracks(zip_file_path):
    print(f"\n\nJamTabaZIPtoTracks by Koshdukai V1.8 (202311)\n\n")

    dest_folder = os.path.splitext(os.path.basename(zip_file_path))[0]

    # Create the destination folder if it doesn't exist
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    print(f"  Tracks will be saved to {dest_folder}\n")

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        # Extract the base folder name (ZIP filename without extension)
        base_folder = os.path.splitext(os.path.basename(zip_file_path))[0]

        # Find the first file with a .json extension (assumed to be the JSON file)
        json_filename = next((file for file in zip_ref.namelist() if file.endswith('.json')), None)
        #json_filename = "clipsort.json"

        # Check if a JSON file was found
        if json_filename is None:
            print("Error: No JSON file found in the ZIP archive.")
            sys.exit(1)

        # Read the JSON file directly from the zip
        with zip_ref.open(json_filename) as json_file:
            json_data = json.load(json_file)

        # Group channels by user
        user_channels = {}
        for entry in json_data:
            for channel in entry["channels"]:
                user = channel["user"]
                chan = channel["chan"]
                user_without_suffix = user.split('@')[0]
                key = (user_without_suffix, chan)

                if key not in user_channels:
                    user_channels[key] = {'intervals': [], 'filenames': [], 'bpm': entry["bpm"]}

                user_channels[key]['intervals'].append(entry["interval"])
                user_channels[key]['filenames'].append(os.path.join(base_folder, channel["fname"]))

        # Initialize the reference duration for silence fill-ins
        reference_duration = None

        # Process each user and channel
        for (user_without_suffix, chan), data in user_channels.items():
            # Sort intervals based on the starting interval
            intervals = sorted(zip(data['intervals'], data['filenames']))

            # Extract BPM and the starting interval from the first entry
            start_interval, filenames = intervals[0]
            bpm = data['bpm']

            # Initialize the list to store AudioSegments
            segments = []

            dest_fname = f"{bpm}bpm.{user_without_suffix}.Chn{chan}.*.mp3"
            dest_filepath = os.path.join(dest_folder, dest_fname)
            check_if_exists = glob.glob(dest_filepath)
            found = 0
            if check_if_exists:
                for dest_filepath in check_if_exists:
                    found = found + 1

            if found > 0:
                print(f"    Skipping track for {user_without_suffix} Channel:{chan} because it already exists\n")
            else:
                print(f"    Generating track for {user_without_suffix} Channel:{chan}:")
                # Process each interval
                interval_count=1
                print("      Interval",end="")
                for interval, fname in intervals:
                    # Read the audio segment from the file and add it to the list
                    segment = AudioSegment.from_file(zip_ref.open(fname), format="ogg")
                    # Update the reference duration if it's not set
                    if reference_duration is None:
                        reference_duration = segment.duration_seconds * 1000  # Convert seconds to milliseconds
                    # Check if there is a gap between the previous interval and the current one
                    if reference_duration is not None and interval>interval_count :
                        # Calculate the number of intervals to fill with silence
                        num_silence_intervals = interval - interval_count

                        # Create a silence segment with the reference duration
                        silence = AudioSegment.silent(duration=reference_duration)

                        print(f" {interval_count} is missing! Inserting {num_silence_intervals} of silence!",end="")
                        interval_count = interval
                        # Add the silence segments to the list
                        segments.extend([silence] * num_silence_intervals)

                    print(f" {interval}",end="")

                    segments.append(segment)

                    # Update the reference duration if it's not set
                    if reference_duration is None:
                        reference_duration = segment.duration_seconds * 1000  # Convert seconds to milliseconds
                    interval_count=interval_count+1

                print(" ")
                # Concatenate the segments
                combined = sum(segments)

                # Create the destination file name
                number_of_intervals = len(intervals)
                #dest_fname = f"{bpm}bpm.{user_without_suffix}.Chn{chan}.{number_of_intervals:04d}intervals.#{start_interval}.mp3"
                dest_fname = f"{bpm}bpm.{user_without_suffix}.Chn{chan}.{number_of_intervals}intervals.started_at_{start_interval}.mp3"
                dest_filepath = os.path.join(dest_folder, dest_fname)

                # Export the combined audio to a new MP3 file
                combined.export(dest_filepath, format="mp3")
                print(f"    Generated track originally with {number_of_intervals} segment files:\n      {dest_filepath}\n")

    print(f"\n  Finished!\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("  Usage: python3 JamTabaZIPtoTracks.py path/to/your_archive.zip")
        sys.exit(1)

    zip_file_path = sys.argv[1]
    generate_tracks(zip_file_path)
