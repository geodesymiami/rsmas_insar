#!/usr/bin/env bash

if [[ "$1" == "--help" || "$1" == "-h" || -z "$1" ]]; then
helptext="                                                                       \n\
  Example:                                                                       \n\
      create_index_html.bash  sbas/pic                                           \n\
                                                                                 \n\
      creates an index.html in the directory and on Mac displays using your  \n\
      default browser (note: you may have to empty your cache occasionaly)  \n\n"  
  printf "$helptext"
  exit 0;
fi

# Directory containing images
dir_of_interest="$1"
# Output HTML file
index_file="$dir_of_interest/index.html"

# Ensure the directory exists
if [ ! -d "$dir_of_interest" ]; then
    echo "Directory does not exist: $dir_of_interest"
    exit 1
fi

# Start of HTML file
cat <<EOF > "$index_file"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Image Gallery</title>
    <style>
        body {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        img {
            max-width: 800px; /* Increase size */
            margin: 10px; /* Reduced margin around images */
            width: 100%;
            height: auto;
        }
        .image-name {
            margin-bottom: 20px; /* Reduced whitespace below image names */
            font-size: 20px;
            color: #333;
        }
    </style>
</head>
<body>
    <h1>Image Gallery</h1>
    <div>
EOF

# Loop through all PNG files in the specified directory and add them to the HTML
for img in "$dir_of_interest"/*.png; do
    # Extract just the filename from the path
    img_name=$(basename "$img")
    # Make sure to reference the image relative to the index.html location
    echo "            <div class=\"image-name\">$img_name</div>" >> "$index_file"
    echo "        <div class=\"image-container\">" >> "$index_file"
    echo "            <a href=\"$img_name\"><img src=\"$img_name\" alt=\"$img_name\"></a>" >> "$index_file"
    echo "        </div>" >> "$index_file"
done

# End of HTML file
cat <<EOF >> "$index_file"
    </div>
</body>
</html>
EOF

# Output command to open the directory or HTML file
echo "Index file created at: $index_file"
#echo "To view the directory, run: open \"$dir_of_interest\""

if [ "$(uname)" == "Darwin" ]; then
   cmd="open \"$index_file\""
   eval "$cmd"
fi
echo "To view the gallery in your browser, run: "
echo "open \"$index_file\""
