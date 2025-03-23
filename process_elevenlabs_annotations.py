import json
import argparse
import sys

def choose_speaker(data):
    """
    Counts occurrences of speakers in the data, filters out speakers with fewer than 20 records,
    displays a numbered list of remaining speakers, and prompts the user to choose one.
    
    Returns:
      The selected speaker's id.
    """
    # Count occurrences for each speaker using speaker_id and speaker_name.
    speaker_counts = {}
    for record in data:
        speaker_id = record.get("speaker_id")
        speaker_name = record.get("speaker_name")
        if speaker_id and speaker_name:
            if speaker_id in speaker_counts:
                speaker_counts[speaker_id]["count"] += 1
            else:
                speaker_counts[speaker_id] = {"name": speaker_name, "count": 1}
    
    # Filter speakers with at least 20 occurrences.
    valid_speakers = {k: v for k, v in speaker_counts.items() if v["count"] >= 20}
    
    if not valid_speakers:
        print("No speakers with at least 20 occurrences found. Exiting.")
        sys.exit(1)
    
    # Create a sorted list of speakers by speaker_id.
    speakers_list = sorted(valid_speakers.items(), key=lambda x: x[0])
    
    print("Choose the speaker to keep:")
    for idx, (speaker_id, info) in enumerate(speakers_list, start=1):
        print(f"{idx} - {speaker_id} ({info['count']})")
    
    # Prompt the user until a valid option is selected.
    while True:
        choice = input("Enter the number corresponding to the speaker: ")
        try:
            choice_int = int(choice)
            if 1 <= choice_int <= len(speakers_list):
                selected_speaker_id = speakers_list[choice_int - 1][0]
                return selected_speaker_id
            else:
                print("Invalid selection. Please choose a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def process_data(data):
    """
    Process the input data to filter, sort, and combine records into sentences.
    
    Steps:
    1. Filter out records that do not have a type of "spacing" or "word".
    2. Sort the filtered records by the "start" time.
    3. Iterate through the records to build sentences:
       - Start a sentence with the current record's text and record its start time.
       - If the current sentence (after stripping) ends with punctuation ('.', '!', '?'), finish the sentence.
       - Otherwise, append the next record's text and update the end time.
    4. Safety check: When the data ends, if the last sentence doesn’t end with punctuation, still add it.
    5. Final pass: Remove any sentence where the "text" field is exactly a single space " ".
       
    Returns:
      A list of dictionaries, each with the keys "text", "start", and "end".
    """
    # Filter out records that are not "spacing" or "word"
    filtered = [record for record in data if record.get("type") in ["spacing", "word"]]
    
    # Sort the filtered records by the "start" key
    filtered.sort(key=lambda x: x.get("start", 0))
    
    sentences = []
    i = 0
    n = len(filtered)
    
    while i < n:
        # Initialize a new sentence using the current record
        current_record = filtered[i]
        sentence_text = current_record.get("text", "")
        sentence_start = current_record.get("start")
        sentence_end = current_record.get("end")
        i += 1
        
        # Build the sentence until a termination condition is met.
        while i < n:
            stripped_text = sentence_text.strip()
            if stripped_text and stripped_text[-1] in ".!?":
                break  # End the sentence if it ends with punctuation.
            
            next_record = filtered[i]
            next_text = next_record.get("text", "")
            sentence_text += next_text
            sentence_end = next_record.get("end")
            i += 1
        
        sentences.append({
            "text": sentence_text,
            "start": sentence_start,
            "end": sentence_end
        })
    
    # Final pass: remove any sentence that is empty or a single space and strip extra spaces.
    processed_sentences = [
        {**s, "text": s.get("text", "").strip()}
        for s in sentences if s.get("text", "").strip() != ""
    ]
    
    return processed_sentences

def main():
    parser = argparse.ArgumentParser(
        description="Process a JSON file to build sentences from text data."
    )
    parser.add_argument("input_file", help="Path to the input JSON file")
    parser.add_argument("output_file", help="Path to the output JSON file")
    args = parser.parse_args()
    
    # Load the JSON data from the input file.
    try:
        with open(args.input_file, "r", encoding="utf-8") as infile:
            data = json.load(infile)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    # Prompt user to select a speaker to keep.
    selected_speaker = choose_speaker(data)
    
    # Filter the data to only include records from the selected speaker.
    filtered_data = [record for record in data if record.get("speaker_id") == selected_speaker]
    
    # Process the filtered data to create sentences.
    processed_data = process_data(filtered_data)
    
    # Write the processed data to the output JSON file.
    try:
        with open(args.output_file, "w", encoding="utf-8") as outfile:
            json.dump(processed_data, outfile, indent=2)
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)
    
    print(f"Processed data saved to {args.output_file}")

if __name__ == "__main__":
    main()
