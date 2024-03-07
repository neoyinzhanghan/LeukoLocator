import openslide

def get_total_levels(ndpi_file_path):
    try:
        # Open the NDPI file
        slide = openslide.OpenSlide(ndpi_file_path)
        
        # Get the total number of levels
        total_levels = slide.level_count
        
        # Close the slide
        slide.close()
        
        return total_levels
    except Exception as e:
        return str(e)

# Replace 'path/to/your/file.ndpi' with the actual path to your NDPI file
ndpi_file_path = 'path/to/your/file.ndpi'
total_levels = get_total_levels(ndpi_file_path)
print(f"Total number of levels in the NDPI file: {total_levels}")
